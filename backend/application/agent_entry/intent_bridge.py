"""L1 · MA 决策 → Intent 桥接（单一职责）。

背景：
  · 现有 agent_entry 用 intent_router.route() 返回 Intent 枚举
  · MA TaskRouter 返回 RouteDecision（agent_id: planner/coder/...）
  · 本桥接把 MA agent_id 翻译成 Intent

映射（保守）：
  planner   → ANALYZE（理解项目）
  coder     → MODIFY（改代码）
  reviewer  → MODIFY（复核也是修改前的动作）
  rag_qa    → QUERY（只读知识问答）
  chat      → None（走原 intent_router 决策）

env:
  RAG_MA_TAKEOVER=1  启用接管（默认 0）
"""
from __future__ import annotations
import os
from typing import Any, Optional

from backend.application.agent_entry.intent_router import Intent


# agent_id → Intent
_MAP = {
    "planner":  Intent.ANALYZE,
    "coder":    Intent.MODIFY,
    "reviewer": Intent.MODIFY,
    "rag_qa":   Intent.QUERY,
    # chat → None（保持原决策）
}

# 置信度阈值：不达则不接管
_MIN_CONFIDENCE = {
    "planner":  0.7,
    "coder":    0.6,
    "reviewer": 0.6,
    "rag_qa":   0.7,
}


def is_enabled() -> bool:
    """接管总开关。"""
    if os.environ.get("RAG_MA_ENABLED", "0") != "1":
        return False
    v = os.environ.get("RAG_MA_TAKEOVER", "0").strip().lower()
    return v in ("1", "true", "yes", "on")


def decide(message: str,
           router: Any = None) -> Optional[Any]:
    """返回 MA 决策（RouteDecision），未启用返回 None。"""
    if not is_enabled():
        return None
    if not message or not message.strip():
        return None
    try:
        if router is None:
            from backend.application.multi_agent import (
                get_default_router)
            router = get_default_router()
        d = router.route(message)
    except Exception:
        return None
    # 兜底（fallback）不接管
    if d is None or d.fallback or not d.chosen:
        return None
    return d


def to_intent(d: Any) -> Optional[Any]:
    """把 MA RouteDecision 映射到 Intent。不映射返回 None。"""
    if d is None or not getattr(d, "chosen", None):
        return None
    aid = d.chosen.agent_id
    intent = _MAP.get(aid)
    if intent is None:
        return None
    # 置信度简单启发式：intent 非 fallback + 有明确 caps → 高
    conf = 0.9 if not d.fallback else 0.4
    if conf < _MIN_CONFIDENCE.get(aid, 0.5):
        return None
    return intent


def takeover(message: str,
             original_intent: Any,
             router: Any = None) -> Any:
    """接管入口：返回最终 intent（MA 命中 → MA intent；否则原 intent）。

    语义：
      · 未启用 takeover → 返回 original_intent（零影响）
      · 启用但 MA 未命中 → 返回 original_intent（fallback）
      · 启用且 MA 命中 → 返回 MA 映射的 intent
    """
    if not is_enabled():
        return original_intent
    try:
        d = decide(message, router=router)
        if d is None:
            return original_intent
        ma_intent = to_intent(d)
        if ma_intent is None:
            return original_intent
        return ma_intent
    except Exception:
        return original_intent


def snapshot() -> dict:
    return {
        "enabled": is_enabled(),
        "map_size": len(_MAP),
        "map": {k: str(v) for k, v in _MAP.items()},
    }


__all__ = ["is_enabled", "decide", "to_intent",
           "takeover", "snapshot"]
