"""图片向量索引契约。职责：只描述图片向量、检索命中、检索报告。
不做向量化（embedder 管）、不索引（indexer 管）、不检索（retriever 管）。
与 rag/multimodal/contracts 边界：
  那层管"文本向量"；本层管"图片向量 / 文搜图 / 图搜图"。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


class SearchMode(str, Enum):
    IMAGE_TO_IMAGE = "image_to_image"   # 图搜图
    TEXT_TO_IMAGE = "text_to_image"     # 文搜图


@dataclass(frozen=True)
class ImageVector:
    """一张图片的向量 + 元信息。"""
    image_id: str
    vector: Tuple[float, ...]
    origin_hash: str = ""
    mime: str = ""
    width: int = 0
    height: int = 0
    text: str = ""                       # 附带的文本描述（可选）
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata",
                           MappingProxyType(dict(self.metadata)))
        if not self.image_id:
            raise ValueError("ImageVector.image_id required")
        if not isinstance(self.vector, tuple):
            raise TypeError("vector must be tuple")
        if not self.vector:
            raise ValueError("vector must not be empty")
        if self.width < 0 or self.height < 0:
            raise ValueError("width/height must be >= 0")

    @property
    def dim(self) -> int:
        return len(self.vector)


@dataclass(frozen=True)
class ImageSearchHit:
    image_id: str
    score: float
    origin_hash: str = ""
    mime: str = ""
    text: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata",
                           MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict:
        return {
            "image_id": self.image_id,
            "score": round(self.score, 6),
            "origin_hash": self.origin_hash,
            "mime": self.mime,
            "text": self.text,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ImageSearchReport:
    query: str
    mode: SearchMode
    hits: Tuple[ImageSearchHit, ...] = ()
    candidates: int = 0
    elapsed_ms: int = 0
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not isinstance(self.hits, tuple):
            raise TypeError("hits must be tuple")

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "mode": self.mode.value,
            "hits": [h.to_dict() for h in self.hits],
            "candidates": self.candidates,
            "elapsed_ms": self.elapsed_ms,
            "meta": dict(self.meta),
        }


__all__ = ["ImageVector", "ImageSearchHit",
           "ImageSearchReport", "SearchMode"]
