"""解析器协议。职责：只定义接口。
不做解析、不注册、不调度。所有具体解析器实现 parse() 返回 SourceDocument。"""
from __future__ import annotations
from typing import Protocol

from backend.rag.ingest.contracts import SourceDocument

class ParserProtocol(Protocol):
    def supports(self, path: str) -> bool: ...
    def parse(self, path: str, *, title: str = "",
              meta: dict | None = None) -> SourceDocument: ...

__all__ = ["ParserProtocol"]
