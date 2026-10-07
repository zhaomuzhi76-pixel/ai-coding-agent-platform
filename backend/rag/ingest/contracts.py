"""RAG 数据采集契约。职责：只描述数据源与解析结果。
不做解析（parsers 管）、不索引（indexer 管）、不切片（chunker 管）。
与 rag/multimodal/contracts.py 边界：
  那层管索引单元；本层管"原始数据源 → 可切片的文本/图片"。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

def _freeze(m: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(m))

class SourceType(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    DOCX = "docx"
    JSONL = "jsonl"
    UNKNOWN = "unknown"

_EXT_MAP = {
    ".pdf": SourceType.PDF,
    ".md": SourceType.MARKDOWN,
    ".markdown": SourceType.MARKDOWN,
    ".txt": SourceType.TEXT,
    ".log": SourceType.TEXT,
    ".html": SourceType.HTML,
    ".htm": SourceType.HTML,
    ".docx": SourceType.DOCX,
    ".jsonl": SourceType.JSONL,
}

def detect_source_type(path: str) -> SourceType:
    p = (path or "").lower()
    for ext, t in _EXT_MAP.items():
        if p.endswith(ext):
            return t
    return SourceType.UNKNOWN

@dataclass(frozen=True)
class ParsedPage:
    """单页/单段解析结果。page_no 从 1 开始；0 表示不分页（MD/TXT）。"""
    text: str
    page_no: int = 0
    section: str = ""
    images: Tuple[str, ...] = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze(self.meta))
        if not isinstance(self.text, str):
            raise TypeError("ParsedPage.text must be str")
        if self.page_no < 0:
            raise ValueError("ParsedPage.page_no must be >= 0")
        if not isinstance(self.images, tuple):
            raise TypeError("ParsedPage.images must be tuple")

@dataclass(frozen=True)
class SourceDocument:
    """一个原始数据源的元信息 + 解析产出。"""
    path: str
    source_type: SourceType
    title: str = ""
    pages: Tuple[ParsedPage, ...] = ()
    file_size: int = 0
    file_hash: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze(self.meta))
        if not self.path.strip():
            raise ValueError("SourceDocument.path required")
        if not isinstance(self.pages, tuple):
            raise TypeError("pages must be tuple")
        if self.file_size < 0:
            raise ValueError("file_size must be >= 0")

    @property
    def total_text_chars(self) -> int:
        return sum(len(p.text) for p in self.pages)

    @property
    def page_count(self) -> int:
        return len(self.pages)

@dataclass(frozen=True)
class IngestReport:
    """采集报告。成功/失败数 + 详细错误 + 耗时。"""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    chunks_indexed: int = 0
    errors: Tuple[str, ...] = ()
    elapsed_ms: int = 0
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", _freeze(self.meta))
        if not isinstance(self.errors, tuple):
            raise TypeError("errors must be tuple")

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "chunks_indexed": self.chunks_indexed,
            "errors": list(self.errors),
            "elapsed_ms": self.elapsed_ms,
            "meta": dict(self.meta),
        }

__all__ = ["SourceType", "SourceDocument", "ParsedPage",
           "IngestReport", "detect_source_type"]
