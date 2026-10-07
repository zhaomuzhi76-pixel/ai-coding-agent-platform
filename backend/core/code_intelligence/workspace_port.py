from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CodeIntelligenceWorkspaceProtocol(Protocol):
    """
    Core-owned workspace-scoped code-intelligence port.

    Runtime/Application consume this port without depending on
    concrete intelligence kernel, facade, index, graph, or analyzer.
    """

    def project_intelligence(self) -> dict[str, object]:
        ...

    def project_summary(self) -> dict[str, object]:
        ...

    def analyze_file(self, path: str) -> dict[str, object]:
        ...

    def build_index(self) -> list[dict[str, object]]:
        ...

    def analyze_project(self) -> dict[str, object]:
        ...

    def analyze_impact(
        self,
        *,
        file: str,
        symbol: str | None = None,
    ) -> dict[str, object]:
        ...

    def build_context(
        self,
        *,
        task: str,
    ) -> dict[str, object]:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, object]:
        ...


__all__ = [
    "CodeIntelligenceWorkspaceProtocol",
]
