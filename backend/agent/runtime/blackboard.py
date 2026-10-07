"""Shared blackboard: structured state + message history."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.agent.runtime.message import AgentMessage


class Blackboard:
    """Shared state for multi-agent execution."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._history: List[AgentMessage] = []

    # ─── key-value state ────────────────────────────────────
    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> List[str]:
        return sorted(self._data.keys())

    def snapshot(self) -> Dict[str, Any]:
        return dict(self._data)

    # ─── message history ────────────────────────────────────
    def post(self, message: AgentMessage) -> None:
        self._history.append(message)

    def history(self) -> List[AgentMessage]:
        return list(self._history)

    def last_by_role(self, role: str) -> Optional[AgentMessage]:
        for msg in reversed(self._history):
            if msg.role == role:
                return msg
        return None

    def count(self) -> int:
        return len(self._history)

    def reset(self) -> None:
        self._data.clear()
        self._history.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "ready": self.ready(),
            "keys": self.keys(),
            "messages": self.count(),
        }
