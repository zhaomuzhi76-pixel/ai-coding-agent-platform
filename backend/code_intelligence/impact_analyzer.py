from __future__ import annotations

from typing import Any

from backend.code_intelligence.graph_provider import GraphProvider


class ImpactAnalyzer:
    """
    Code modification impact analysis service.

    Responsibility:
        - analyze change impact
        - detect affected symbols
        - estimate change risk

    Not Responsible:
        - source parsing
        - graph building
        - indexing
        - patch generation
        - modification
        - persistence
    """

    VERSION = "4.1"

    RESPONSIBILITY = (
        "industrial_change_impact_analysis"
    )

    def __init__(self) -> None:
        self.analysis_count = 0

    def analyze(
        self,
        *,
        file: str,
        symbol: str | None = None,
        graph: GraphProvider | None = None,
    ) -> dict[str, Any]:
        self.analysis_count += 1

        affected = self._find_related(
            graph,
            file,
            symbol,
        )

        return {
            "file": file,
            "symbol": symbol,
            "affected_symbols": affected,
            "impact_size": len(affected),
            "risk": self._risk(affected),
            "dependency": {
                "graph_available": graph is not None,
            },
        }

    @staticmethod
    def _find_related(
        graph: GraphProvider | None,
        file: str,
        symbol: str | None,
    ) -> list[str]:
        if graph is None or not symbol:
            return []

        return list(
            graph.find_related(
                f"{file}:{symbol}"
            )
            or []
        )

    @staticmethod
    def _risk(
        affected: list[str],
    ) -> str:
        size = len(affected)

        if size == 0:
            return "low"

        if size <= 5:
            return "medium"

        return "high"

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "metrics": {
                "analysis": self.analysis_count,
            },
            "capabilities": [
                "symbol_impact",
                "risk_estimation",
            ],
        }

__all__ = [
    "ImpactAnalyzer",
]
