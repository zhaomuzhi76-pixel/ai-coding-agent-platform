"""LLM 意图分类器（单一职责：复杂/模糊 query 走 LLM 判 agent）。

双路径：关键词（TaskRouter）→ 命中即返回；未命中 → LLM。
LLM 失败/超时 → 返回 None（调用方兜底）。

env:
  RAG_MA_LLM_INTENT=1       启用（默认 0）
  RAG_MA_LLM_TIMEOUT=15     超时秒
  RAG_MA_LLM_MODEL          LLM 模型（默认 qwen3.5:4b）
"""
from __future__ import annotations
import json
import os
import re
from typing import Optional

_CANDIDATES = ("planner", "coder", "reviewer", "rag_qa", "chat")

_SYSTEM = (
    "你是意图分类器。把用户任务分到以下 agent 之一，只输出 JSON。\n"
    "agent 说明：\n"
    "- planner: 规划/设计/拆解复杂任务\n"
    "- coder: 写代码/改代码/新建文件\n"
    "- reviewer: 审核代码/检查质量\n"
    "- rag_qa: 知识问答/中医/药材/查资料\n"
    "- chat: 闲聊/简单对话\n"
    '输出格式: {"agent": "<id>", "confidence": 0.0-1.0}'
)


def is_enabled() -> bool:
    v = os.environ.get("RAG_MA_LLM_INTENT", "0").strip().lower()
    return v in ("1", "true", "yes", "on")


def _timeout() -> float:
    try:
        return float(os.environ.get("RAG_MA_LLM_TIMEOUT", "15"))
    except ValueError:
        return 15.0


def _model() -> str:
    return os.environ.get("RAG_MA_LLM_MODEL", "qwen3.5:4b")


def _parse(raw: str) -> Optional[dict]:
    if not raw:
        return None
    try:
        o = json.loads(raw.strip())
        if isinstance(o, dict) and o.get("agent") in _CANDIDATES:
            return o
    except Exception:
        pass
    m = re.search(r'\{[^{}]*"agent"\s*:\s*"([^"]+)"[^{}]*\}', raw)
    if m and m.group(1) in _CANDIDATES:
        return {"agent": m.group(1), "confidence": 0.7}
    return None


def classify(message: str) -> Optional[dict]:
    if not is_enabled():
        return None
    text = (message or "").strip()
    if not text:
        return None
    try:
        from backend.providers.runtime.ollama_client import OllamaClient
        c = OllamaClient(timeout=_timeout())
        r = c.chat(
            model=_model(),
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": text[:500]},
            ],
        )
        parsed = _parse(getattr(r, "text", "") or "")
        if parsed:
            parsed["source"] = "llm"
            return parsed
    except Exception:
        return None
    return None


def snapshot() -> dict:
    return {"enabled": is_enabled(), "timeout_s": _timeout(),
            "model": _model(), "candidates": list(_CANDIDATES)}


__all__ = ["is_enabled", "classify", "snapshot"]
