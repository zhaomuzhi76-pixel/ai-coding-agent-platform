"""Part 2 of chat_loop.py."""
from __future__ import annotations
from .part1 import (Any, DEFAULT_MAX_TOOL_STEPS, DEFAULT_TIMEOUT, Mapping, Optional, SessionHistory, ToolCall, ToolExecutor, ToolRegistry, asyncio, get_default_history,)  # noqa
from .part1 import ChatTurnResult  # noqa
from .part1 import _build_system  # noqa
from .part1 import _extract_json  # noqa
import time as _time  # noqa
import os as _os  # noqa
import logging as _logging  # noqa

_log = _logging.getLogger(__name__)
_EVIDENCE_ENABLED = _os.environ.get("RAG_CHAT_EVIDENCE_ENABLED", "1") == "1"

async def run_chat_turn(
    *,
    session_id: str,
    user_text: str,
    gateway: Any,
    provider: str,
    model: str,
    executor: ToolExecutor,
    registry: ToolRegistry,
    history: Optional[SessionHistory] = None,
    max_steps: int = DEFAULT_MAX_TOOL_STEPS,
    timeout: float = DEFAULT_TIMEOUT,
) -> ChatTurnResult:
    if not session_id.strip():
        return ChatTurnResult("", "", ok=False, error="session_id required")
    if not user_text.strip():
        return ChatTurnResult(session_id, "", ok=False, error="empty user_text")
    if gateway is None:
        return ChatTurnResult(session_id, "", ok=False, error="gateway required")

    hist = history or get_default_history()

    # [EVIDENCE-FIRST] 先收集 RAG 证据（env 可关）
    _t0 = _time.time()
    _evidence = None
    _evidence_hint = ""
    _refused_answer = ""
    _refused_reason = ""
    if _EVIDENCE_ENABLED:
        try:
            from backend.agent_tools.chat_evidence import (
                collect as _collect_ev, build_hint as _build_hint)
            # [多轮] 拿历史 user 消息做 query 改写
            _hist_msgs = hist.messages(session_id)
            _hist_users = [m.get("content", "") for m in _hist_msgs
                           if isinstance(m, dict) and m.get("role") == "user"]
            # [BUG3_FIX] evidence 收集在本轮 append 之前 → 无需 [:-1]
            # 保留全部上轮 user（供 rewrite_query 提取实体）
            _evidence = _collect_ev(user_text,
                                     history_texts=_hist_users)
            if _evidence.refused:
                _refused_answer = _refused_answer or (
                    "暂无对应资料")
                _refused_reason = _evidence.reason
            else:
                _evidence_hint = _build_hint(_evidence)
        except Exception as e:
            _log.warning("[chat_loop] evidence 收集失败: %r", e)

    # 拒答：直接返回，不走 LLM（工业级：无证据不生成）
    if _refused_answer:
        hist.append_user(session_id, user_text)
        hist.append_assistant(session_id, _refused_answer,
                               meta={"refused": True, "reason": _refused_reason})
        _ms = int((_time.time() - _t0) * 1000)
        try:
            from backend.agent_tools.chat_trace import get_trace
            get_trace().record(
                session_id=session_id, query=user_text,
                answer=_refused_answer, evidence_count=0,
                confidence=0.0, refused=True, tool_calls=0, steps=0,
                latency_ms=_ms, meta={"reason": _refused_reason})
        except Exception:
            pass
        _imgs = _collect_images(_evidence, [])
        return ChatTurnResult(session_id, _refused_answer, (),
                              0, True, "", images=_imgs)

    # 有证据 → hint 注入到 user_text（不改历史原文）
    # [FIX] history 只存原始 user_text，hint 不污染历史
    hist.append_user(session_id, user_text)

    messages: list[dict] = [
        {"role": "system", "content": _build_system(registry, max_steps)},
    ]
    # [FIX] 截断到最近 20 条（~10 轮），防 context 爆炸
    _recent = hist.messages(session_id)[-20:]
    if _recent and _recent[-1].get("role") == "user" and _evidence_hint:
        _recent[-1] = {"role": "user", "content": user_text + _evidence_hint}
    messages.extend(_recent)

    trace: list[dict] = []

    for step in range(1, max_steps + 1):
        try:
            raw = await asyncio.wait_for(
                gateway.chat(provider, messages, model), timeout=timeout)
        except asyncio.TimeoutError:
            err = f"LLM timeout ({timeout}s)"
            hist.append_assistant(session_id, f"（系统错误：{err}）")
            return ChatTurnResult(session_id, "", tuple(trace), step - 1, False, err)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            hist.append_assistant(session_id, f"（系统错误：{err}）")
            return ChatTurnResult(session_id, "", tuple(trace), step - 1, False, err)

        action = _extract_json(str(raw))
        if action is None:
            answer = str(raw).strip()[:2000] or "(无回答)"
            answer = _finalize_answer(user_text, answer, _evidence)
            hist.append_assistant(session_id, answer)
            _record_trace(session_id, user_text, answer, _evidence,
                          trace, step, _t0)
            _imgs = _collect_images(_evidence, trace)
            return ChatTurnResult(session_id, answer, tuple(trace),
                                  step, True, images=_imgs)

        if action.get("done") is True:
            answer = str(action.get("answer", "")).strip() or "(无回答)"
            # 剥壳：LLM 有时把整个 JSON 塞进 answer 字段
            inner = _extract_json(answer)
            if (isinstance(inner, dict)
                    and isinstance(inner.get("answer"), str)
                    and inner["answer"].strip()):
                answer = inner["answer"].strip()
            answer = _finalize_answer(user_text, answer, _evidence)
            hist.append_assistant(session_id, answer,
                                    meta={"steps": step, "tools": len(trace)})
            _record_trace(session_id, user_text, answer, _evidence,
                          trace, step, _t0)
            _imgs = _collect_images(_evidence, trace)
            return ChatTurnResult(session_id, answer, tuple(trace),
                                  step, True, images=_imgs)

        name = str(action.get("action", "")).strip()
        args = action.get("args") or {}
        if not isinstance(args, Mapping):
            args = {}
        if not name:
            messages.append({"role": "assistant", "content": str(raw)})
            messages.append({"role": "user", "content": "工具结果：\nERROR: 缺 action 字段"})
            continue

        result = executor.execute(ToolCall(name=name, arguments=dict(args)))
        # 兼容 async provider（如 MCP 远端工具）
        if hasattr(result, "__await__"):
            result = await result
        obs = (result.output or result.error or "")[:1500]
        trace.append({"step": step, "action": name, "args": dict(args),
                      "ok": result.ok, "observation": obs[:400],
                      "meta": dict(getattr(result, "meta", None) or {})})
        messages.append({"role": "assistant", "content": str(raw)})
        messages.append({"role": "user", "content": f"工具结果：\n{obs}"})

    # 超步数
    summary = "（已达工具调用上限，请基于已有信息回答或换个问法）"
    hist.append_assistant(session_id, summary)
    _record_trace(session_id, user_text, summary, _evidence, trace,
                  max_steps, _t0)
    _imgs = _collect_images(_evidence, trace)
    return ChatTurnResult(session_id, summary, tuple(trace),
                          max_steps, True, images=_imgs)


def _finalize_answer(user_text, answer, evidence):
    """[INDUSTRIAL] 答案校验 + 规则补全（策略 B）。异常静默。"""
    try:
        from backend.agent_tools.answer_validator import check_and_patch
        hits = list(evidence.hits) if evidence else []
        r = check_and_patch(user_text, answer, hits)
        if not r.ok:
            _log.info("[validator] 补全: %s", r.reason)
        return r.answer
    except Exception as e:
        _log.warning("[validator] 校验失败: %r", e)
        return answer


def _record_trace(session_id, user_text, answer, evidence, trace, steps, t0):
    """[TRACE] 记录本次对话（异常静默）。"""
    try:
        from backend.agent_tools.chat_trace import get_trace
        ev_count = len(evidence.hits) if evidence else 0
        conf = float(evidence.confidence) if evidence else 0.0
        get_trace().record(
            session_id=session_id, query=user_text, answer=answer,
            evidence_count=ev_count, confidence=conf,
            refused=False, tool_calls=len(trace), steps=steps,
            latency_ms=int((_time.time() - t0) * 1000))
    except Exception as e:
        _log.warning("[chat_trace] 记录失败: %r", e)



def _collect_images(evidence, trace) -> tuple:
    """[MM] 从 evidence + trace.meta 里聚合图片（去重，上限 10）。"""
    seen = set()
    out = []
    def _push(im):
        if not isinstance(im, dict):
            return
        k = str(im.get("id") or im.get("url") or "")
        if not k or k in seen:
            return
        seen.add(k)
        out.append({k2: im.get(k2) for k2 in
                    ("id", "mime", "url", "b64", "alt_text", "class_name")})
    # 1) evidence.images 优先
    if evidence is not None:
        for im in (getattr(evidence, "images", ()) or ()):
            _push(im)
    # 2) trace.meta.images 兜底
    for t in (trace or ()):
        for im in ((t.get("meta") or {}).get("images") or ()):
            _push(im)
    return tuple(out[:10])

__all__ = ["ChatTurnResult", "run_chat_turn", "DEFAULT_MAX_TOOL_STEPS"]
