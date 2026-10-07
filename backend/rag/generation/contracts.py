"""生成层契约：GroundedAnswer / Citation"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    idx: int
    chunk_id: str
    source: str
    page: int = 0
    score: float = 0.0
    excerpt: str = ""


@dataclass(frozen=True)
class GroundedAnswer:
    query: str
    answer: str
    citations: tuple
    confidence: float
    refused: bool
    reason: str = ""
    context_text: str = ""

    @property
    def has_answer(self) -> bool:
        return bool(self.answer) and not self.refused


__all__ = ["Citation", "GroundedAnswer"]
