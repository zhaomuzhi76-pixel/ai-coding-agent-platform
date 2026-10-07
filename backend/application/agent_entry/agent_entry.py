"""统一 Agent 入口：按意图分发。

- query     → 只读快通道（不走 LLM）
- analyze   → Agent 循环（理解项目）
- modify    → Agent 循环（改代码）
- create    → Agent 循环（脚手架）
"""
from __future__ import annotations
from backend.core.model_registry.legacy_compat import _default_role_model, _default_provider_id

from typing import Any

from backend.application.agent_loop import run_agent_loop
from backend.providers.config import load_llm_config

from .intent_router import Intent, route
from .query_handler import handle_query

DEFAULT_MAX_STEPS = 10
DISPATCH_TIMEOUT_SEC = 300  # 5 分钟硬上限


def _resolve_provider_name(provider: str, model: str) -> str:
    """把前端契约类型映射到配置里的真实 provider 名。

    前端 toLegalProvider 传 "ollama" / "openai_compatible"，
    配置里是 _default_provider_id() / "dashscope-qwen" / "dashscope-maas"。
    优先按 model 名反查（model 全局唯一）。
    """
    cfg = load_llm_config()
    names = [p.name for p in cfg.providers]
    print(
        f"[agent-entry] resolve provider={provider!r} "
        f"model={model!r} configured={names}",
        flush=True,
    )

    print(f"[resolve-diag] provider={provider!r} model={model!r}", flush=True)

    # 1. provider 名直接命中
    for p in cfg.providers:
        if p.name == provider:
            return provider

    # 2. 按 model 名反查（最可靠）
    if model:
        for p in cfg.providers:
            for m in p.models:
                if m.id == model:
                    print(
                        f"[agent-entry] model matched → {p.name}/{m.id}",
                        flush=True,
                    )
                    return p.name

    # 3. provider 匹配配置 type
    for p in cfg.providers:
        if p.type == provider:
            print(
                f"[agent-entry] type matched → {p.name}/{model}",
                flush=True,
            )
            return p.name

    print(f"[agent-entry] fallback → {provider}/{model}", flush=True)
    return provider


async def dispatch(
    payload: dict[str, Any],
    session: Any,
    gateway: Any = None,
    on_step: Any = None,
) -> dict[str, Any] | None:
    message = str(payload.get("message", ""))


    # [MA-OBS] Multi-Agent 观测（env RAG_MA_ENABLED=1 生效 · 不改流程）
    try:
        import os as _os_ma
        if _os_ma.environ.get("RAG_MA_ENABLED", "0") == "1":
            from backend.application.multi_agent import (
                get_default_router as _gdr,
            )
            _ma_d = _gdr().route(message)
            import logging as _lg_ma
            _lg_ma.getLogger(__name__).info(
                "[MA-route] agent=%s role=%s intent=%s fallback=%s",
                _ma_d.agent_id,
                _ma_d.chosen.role if _ma_d.chosen else "-",
                _ma_d.intent, _ma_d.fallback)
            if isinstance(globals().get("_MA_OBS_LOG"), list):
                _MA_OBS_LOG.append({
                    "agent": _ma_d.agent_id,
                    "role": _ma_d.chosen.role if _ma_d.chosen else "",
                    "intent": _ma_d.intent,
                    "fallback": _ma_d.fallback,
                    "reason": _ma_d.reason,
                    "message": message[:80],
                })
    except Exception:
        pass
    # ── 工业级：用户消息 → 自动学习规则（持久化）──
    try:
        from backend.agent_learning.auto_learner import get_default
        workspace = str(
            payload.get("workspace", "")
            or getattr(session, "workspace", "")
            or ""
        )
        learned = get_default().learn_from_message(
            message, workspace=workspace,
        )
        if learned:
            print(
                f"[auto-learn] {len(learned)} 条规则: "
                f"{[r['key'] for r in learned]}",
                flush=True,
            )
    except Exception as e:
        print(f"[auto-learn] error: {e}", flush=True)
    workspace = str(
        payload.get("workspace", "")
        or getattr(session, "workspace", "")
        or getattr(session, "root_path", "")
        or ""
    )
    domains = payload.get("domains") or []
    model = str(payload.get("model", "") or "")
    provider = str(payload.get("provider", "") or "")

    intent = route(message)

    # [MA-TAKEOVER] MA 决策覆盖 intent（env 三级 · 默认零影响）
    try:
        from backend.application.agent_entry.intent_bridge import (
            takeover as _ma_takeover,
        )
        intent = _ma_takeover(message, intent)
    except Exception:
        pass

    if intent == Intent.QUERY:
        return await handle_query(message, workspace, on_step=on_step)

    if gateway is None:
        return {
            "success": False,
            "error": "agent loop requires LLM gateway",
            "intent": intent,
        }

    # === 空 model → 从 Model Registry 的角色配置里取 ===
    if not model:
        try:
            from backend.core.model_registry.registry import get_registry
            reg = get_registry()
            # 意图 → 角色映射
            role_map = {
                Intent.ANALYZE: "plan",
                Intent.MODIFY:  "code",
                Intent.CREATE:  "code",
            }
            role = role_map.get(intent, "code")
            route_obj = reg.roles.get(role)
            if route_obj and route_obj.primary:
                m = reg.models.get(route_obj.primary)
                if m:
                    model = m.id
                    provider = m.provider_id
                    print(
                        f"[agent-entry] 跟随角色配置 role={role} "
                        f"-> {provider}/{model}",
                        flush=True,
                    )
                else:
                    print(
                        f"[agent-entry] role={role} 的模型 "
                        f"{route_obj.primary!r} 未注册",
                        flush=True,
                    )
            else:
                print(
                    f"[agent-entry] role={role} 未配置，回退默认",
                    flush=True,
                )
        except Exception as e:
            print(f"[agent-entry] follow role error: {e}", flush=True)

    real_provider = _resolve_provider_name(
        provider or "ollama", model,
    )

    import asyncio
    try:
        result = await asyncio.wait_for(
            run_agent_loop(
                task=message,
                workspace=workspace,
                gateway=gateway,
                provider=real_provider,
                model=model or "",
                max_steps=DEFAULT_MAX_STEPS,
                on_step=on_step,
                domains=domains,
            ),
            timeout=DISPATCH_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": f"dispatch timeout ({DISPATCH_TIMEOUT_SEC}s)",
            "intent": intent,
        }
    result["intent"] = intent
    return result


_MA_OBS_LOG = []  # MA-OBS-BUFFER

__all__ = ["dispatch"]
