from __future__ import annotations

from typing import Any


class WorkspaceResponsibilityAnalyzer:
    """
    Workspace responsibility conflict analyzer.

    Responsibility:
        - detect duplicate module responsibilities
        - analyze workspace responsibility conflicts

    Not Responsible:
        - source parsing
        - code modification
        - responsibility report generation
    """

    VERSION = "7.0"

    RESPONSIBILITY = (
        "workspace_responsibility_conflict_analysis"
    )

    MIN_FILES = 2

    def analyze(
        self,
        modules: list[dict[str, Any]],
    ) -> dict[str, Any]:

        groups: dict[str, list] = {}

        for module in modules:

            for name in module.get(
                "responsibilities",
                [],
            ):
                groups.setdefault(
                    name,
                    [],
                ).append(
                    module
                )

        conflicts = []

        for name, items in groups.items():

            if len(items) < self.MIN_FILES:
                continue

            conflicts.append(
                self._build(
                    name,
                    items,
                )
            )

        return {
            "duplicate_responsibility":
                conflicts,

            "summary": {
                "detected":
                    len(conflicts),
            },
        }

    def _build(
        self,
        name: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:

        return {
            "type":
                "possible_duplicate_responsibility",

            "responsibility":
                name,

            "domains":
                sorted(
                    {
                        item.get(
                            "domain",
                            "unknown",
                        )
                        for item in items
                    }
                ),

            "files":
                [
                    item.get(
                        "path",
                        "",
                    )
                    for item in items
                ],

            "count":
                len(items),
        }

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "WorkspaceResponsibilityAnalyzer",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                True,
        }


__all__ = [
    "WorkspaceResponsibilityAnalyzer",
]
