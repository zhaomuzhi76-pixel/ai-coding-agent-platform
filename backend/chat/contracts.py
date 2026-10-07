"""多轮对话契约。"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class ChatTurn:
    turn_id: str = field(default_factory=lambda: "ct-" + uuid.uuid4().hex[:10])
    user_text: str = ""
    user_images: Tuple[str, ...] = ()
    reply_text: str = ""
    reply_images: Tuple[str, ...] = ()
    domain: str = ""
    rag_hits: int = 0
    verdict: str = ""
    reason: str = ""
    created_at: float = field(default_factory=time.time)

    def to_llm_pair(self) -> Tuple[str, str]:
        u = self.user_text
        if self.user_images:
            u = f"{u} [附图×{len(self.user_images)}]" if u else f"[附图×{len(self.user_images)}]"
        return u, self.reply_text


@dataclass
class Conversation:
    session_id: str
    turns: List[ChatTurn] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def append(self, turn: ChatTurn) -> None:
        self.turns.append(turn)

    def last_n(self, n: int) -> List[ChatTurn]:
        return self.turns[-n:] if n > 0 else []

    def total_turns(self) -> int:
        return len(self.turns)


__all__ = ["ChatTurn", "Conversation"]
