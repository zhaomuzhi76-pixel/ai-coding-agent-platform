"""带预取的 chat_loop 包装。职责：
  ① 对 user_text 跑 matcher
  ② 命中 → 调对应工具 → 结果作为 hint 拼进 user_text
  ③ 调原 run_chat_turn（chat_loop.py 一行不动）
不匹配（matcher 管）、不执行工具细节（executor 管）、不做响应组装。
历史会带上 hint（可接受；如需清洗由 SessionHistory 层加接口）。"""
from __future__ import annotations
from typing import Any, Optional

from backend.agent_tools.contracts import ToolCall
from backend.agent_tools.trigger.contracts import TriggerMatch
from backend.agent_tools.trigger.matcher import TriggerMatcher, get_default_matcher

PREFETCH_MAX_CHARS = 1200
HINT_TPL = (
    "\n\n【系统已自动调用 `{tool}` 获取以下资料 — "
    "请优先基于它回答；如信息不足可再调其他工具】\n{output}"
)

async def _prefetch(match: TriggerMatch, executor: Any) -> Optional[str]:
    try:
        r = executor.execute(ToolCall(name=match.tool,
                                       arguments=dict(match.arguments)))
        if hasattr(r, "__await__"):
            r = await r
    except Exception:
        return None
    if r is None or not getattr(r, "ok", False):
        return None
    text = (getattr(r, "output", "") or "").strip()
    if not text:
        return None
    return text[:PREFETCH_MAX_CHARS]

async def run_chat_turn_with_prefetch(
    *,
    session_id: str,
    user_text: str,
    gateway: Any,
    provider: str,
    model: str,
    executor: Any,
    registry: Any,
    history: Any = None,
    matcher: Optional[TriggerMatcher] = None,
) -> Any:
    from backend.agent_tools.chat_loop import run_chat_turn

    m = matcher or get_default_matcher()
    match = m.match(user_text, registry=registry)
    hint = ""
    if match is not None:
        out = await _prefetch(match, executor)
        if out:
            hint = HINT_TPL.format(tool=match.tool, output=out)

    return await run_chat_turn(
        session_id=session_id,
        user_text=user_text + hint,
        gateway=gateway, provider=provider, model=model,
        executor=executor, registry=registry, history=history)

__all__ = ["run_chat_turn_with_prefetch",
           "PREFETCH_MAX_CHARS", "HINT_TPL"]
