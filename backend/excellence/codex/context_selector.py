"""Token-budget context selector (Codex: 上下文约束).

从多候选文件/片段中按优先级裁剪到 token 预算。
复用冻结层：无（纯字符串级预算管理）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence


@dataclass
class ContextChunk:
    source: str          # 文件路径或标识
    content: str
    priority: float = 0.5
    label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def char_len(self) -> int:
        return len(self.content)


@dataclass
class SelectedContext:
    chunks: List[ContextChunk] = field(default_factory=list)
    dropped: List[ContextChunk] = field(default_factory=list)
    used_chars: int = 0
    budget_chars: int = 0

    @property
    def coverage(self) -> float:
        if not self.chunks and not self.dropped:
            return 1.0
        total = len(self.chunks) + len(self.dropped)
        return len(self.chunks) / total if total else 1.0

    def render(self, separator: str = "\n\n") -> str:
        return separator.join(c.content for c in self.chunks)

    def dump(self) -> Dict[str, Any]:
        return {
            "selected": [c.source for c in self.chunks],
            "dropped": [c.source for c in self.dropped],
            "used_chars": self.used_chars,
            "budget_chars": self.budget_chars,
            "coverage": round(self.coverage, 3),
        }


class ContextSelector:
    """Select chunks to fit a char budget (approximates token budget)."""

    VERSION = "1.0"

    def __init__(
        self,
        budget_chars: int = 32000,
        chars_per_token: float = 4.0,
    ) -> None:
        if budget_chars <= 0:
            raise ValueError("budget_chars must positive")
        self._budget = budget_chars
        self._cpt = chars_per_token

    def select(
        self, chunks: Sequence[ContextChunk],
    ) -> SelectedContext:
        ranked = sorted(chunks, key=lambda c: -c.priority)
        out = SelectedContext(budget_chars=self._budget)
        remaining = self._budget
        for c in ranked:
            if c.char_len <= remaining:
                out.chunks.append(c)
                remaining -= c.char_len
            else:
                out.dropped.append(c)
        out.used_chars = self._budget - remaining
        return out

    def tokens_estimate(self, chars: int) -> int:
        return int(chars / self._cpt) if self._cpt else chars

    def ready(self) -> bool:
        return self._budget > 0

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "budget_chars": self._budget,
        }


__all__ = ["ContextChunk", "SelectedContext", "ContextSelector"]
