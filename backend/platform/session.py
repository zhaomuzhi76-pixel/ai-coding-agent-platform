"""CodingSession: multi-turn coding session state."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionTurn:
    turn_id: str
    role: str  # user | system | agent
    content: str
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class CodingSession:
    """Multi-turn coding session: history + workspace + locale + model."""

    VERSION = "1.0"

    def __init__(
        self,
        *,
        workspace: str = "",
        user_id: str = "",
        locale: str = "zh-CN",
        model: str = "",
        session_id: Optional[str] = None,
    ) -> None:
        self.session_id = session_id or uuid.uuid4().hex[:16]
        self.workspace = workspace
        self.user_id = user_id
        self.locale = locale
        self.model = model
        self.created_at = time.time()
        self.updated_at = self.created_at
        self._turns: List[SessionTurn] = []
        self._metadata: Dict[str, Any] = {}

    # ─── turn management ────────────────────────────────────
    def add_turn(
        self, role: str, content: str, **metadata: Any,
    ) -> SessionTurn:
        if not role.strip():
            raise ValueError("role required")
        if not isinstance(content, str):
            raise TypeError("content must str")
        turn = SessionTurn(
            turn_id=uuid.uuid4().hex[:12],
            role=role.strip(),
            content=content,
            metadata=dict(metadata),
        )
        self._turns.append(turn)
        self.updated_at = turn.created_at
        return turn

    def turns(self) -> List[SessionTurn]:
        return list(self._turns)

    def last_user_turn(self) -> Optional[SessionTurn]:
        for t in reversed(self._turns):
            if t.role == "user":
                return t
        return None

    def turn_count(self) -> int:
        return len(self._turns)

    # ─── context extraction ─────────────────────────────────
    def recent_context(self, limit: int = 5) -> str:
        """Compact recent turns for prompt injection."""
        recent = self._turns[-limit:]
        lines: List[str] = []
        for t in recent:
            lines.append(f"[{t.role}] {t.content[:200]}")
        return "\n".join(lines)

    # ─── metadata ───────────────────────────────────────────
    def set(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)

    # ─── lifecycle ──────────────────────────────────────────
    def touch(self) -> None:
        self.updated_at = time.time()

    def ready(self) -> bool:
        return bool(self.session_id and self.workspace)

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "session_id": self.session_id,
            "workspace": self.workspace,
            "user_id": self.user_id,
            "locale": self.locale,
            "model": self.model,
            "turns": self.turn_count(),
            "created_at": self.created_at,
        }


__all__ = ["SessionTurn", "CodingSession"]
