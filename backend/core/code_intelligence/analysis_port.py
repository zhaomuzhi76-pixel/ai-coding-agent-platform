from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CodeAnalyzerProtocol(Protocol):
    """
    Core-owned source-analysis port.

    Runtime/tool consumers depend only on this port.
    """

    def analyze(
        self,
        source: str,
    ) -> object:
        ...

    def ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "CodeAnalyzerProtocol",
]
