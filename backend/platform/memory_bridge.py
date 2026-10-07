"""MemoryBridge: feed platform outcomes into memory learning loop.

复用冻结层：
    code_intelligence.memory.FeedbackLoop  -> 全局记忆 (skill + preference)
    code_intelligence.memory.MemoryStore   -> 项目记忆
    code_intelligence.memory.SessionLog    -> 会话日志

本桥只做「把 platform 事件翻译成记忆层调用」，不重造任何记忆能力。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any, Dict, List, Optional


class MemoryBridge:
    VERSION = "1.0"

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._accept_count = 0
        self._reject_count = 0

    def on_accept(
        self,
        *,
        task: str,
        plan: str,
        changes: List[Dict[str, Any]],
        workspace: str,
        model: str = "",
        attempts: int = 1,
    ) -> None:
        self._accept_count += 1
        if not self._enabled or not changes:
            return
        try:
            from backend.code_intelligence.memory import FeedbackLoop
            summary_kind = (
                changes[0].get("kind", "") if changes else ""
            )
            summary_text = "\n".join(
                f"=== {c.get('file', '?')} ===\n{c.get('text', '')}"
                for c in changes
            )
            FeedbackLoop().on_accept(
                task=task, plan=plan,
                kind=str(summary_kind), text=summary_text,
                workspace=workspace,
            )
        except Exception as e:
            swallow("platform.memory_bridge:52", e)

    def on_reject(
        self,
        *,
        task: str,
        plan: str,
        changes: List[Dict[str, Any]],
        workspace: str,
        feedback: str = "",
    ) -> None:
        self._reject_count += 1
        if not self._enabled or not changes:
            return
        try:
            from backend.code_intelligence.memory import FeedbackLoop
            summary_kind = (
                changes[0].get("kind", "") if changes else ""
            )
            summary_text = "\n".join(
                f"=== {c.get('file', '?')} ===\n{c.get('text', '')}"
                for c in changes
            )
            FeedbackLoop().on_reject(
                task=task, plan=plan,
                kind=str(summary_kind), text=summary_text,
                workspace=workspace,
                feedback=feedback,
            )
        except Exception as e:
            swallow("platform.memory_bridge:82", e)

    def accept_count(self) -> int:
        return self._accept_count

    def reject_count(self) -> int:
        return self._reject_count

    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, flag: bool) -> None:
        self._enabled = bool(flag)

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "enabled": self._enabled,
            "accepts": self._accept_count,
            "rejects": self._reject_count,
        }


__all__ = ["MemoryBridge"]
