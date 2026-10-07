from __future__ import annotations

from typing import Any

from backend.workspace.responsibility_analyzer import (
    WorkspaceResponsibilityAnalyzer,
)

from backend.workspace.responsibility_registry import (
    ResponsibilityRegistry,
)

from backend.workspace.responsibility_similarity import (
    ResponsibilitySimilarity,
)


class WorkspaceBoundaryGuard:
    """
    Workspace responsibility boundary validator.

    Responsibility:
        - coordinate responsibility validation
        - detect responsibility conflicts
        - expose validation decision

    Not Responsible:
        - responsibility conflict validation
        - code parsing
        - filesystem access
        - code modification
    """

    VERSION = "8.1"

    RESPONSIBILITY = (
        "workspace_boundary_guard"
    )

    def __init__(
        self,
        registry: ResponsibilityRegistry | None = None,
        similarity: ResponsibilitySimilarity | None = None,
        analyzer: WorkspaceResponsibilityAnalyzer | None = None,
    ) -> None:

        self.registry = (
            registry
            or ResponsibilityRegistry()
        )

        self.similarity = (
            similarity
            or ResponsibilitySimilarity()
        )

        self.analyzer = (
            analyzer
            or WorkspaceResponsibilityAnalyzer()
        )

    def check(
        self,
        profile: dict[str, Any],
    ) -> dict[str, Any]:

        conflicts = []

        for item in self.registry.all():

            score = self.similarity.calculate(
                profile,
                item,
            )

            if score >= 0.5:

                conflicts.append(
                    {
                        "path":
                            item.get(
                                "path",
                                "",
                            ),

                        "similarity":
                            score,
                    }
                )

        analysis = self.analyzer.analyze(
            [
                *self.registry.all(),
                profile,
            ]
        )

        return {
            "allowed":
                not conflicts
                and not analysis.get(
                    "duplicate_responsibility",
                    [],
                ),

            "conflicts":
                conflicts,

            "analysis":
                analysis,

        }

    def register(
        self,
        profile: dict[str, Any],
    ) -> None:

        self.registry.register(
            profile
        )

    def ready(
        self,
    ) -> bool:

        return (
            self.registry.ready()
            and self.similarity.ready()
            and self.analyzer.ready()
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "WorkspaceBoundaryGuard",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "WorkspaceBoundaryGuard",
]
