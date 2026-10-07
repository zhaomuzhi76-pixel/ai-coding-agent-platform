from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.utils.time import now_iso

class CodeContextBuilder:
    """
    Build LLM-ready code intelligence context.

    Responsibility:
        - assemble code context
        - combine task information
        - prepare reasoning input

    Not Responsible:
        - code parsing
        - indexing
        - retrieval
        - patch generation
        - file modification
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "industrial_code_context_assembly"
    )

    def __init__(
        self,
    ) -> None:

        self.build_count = 0

    def build(
        self,
        *,
        task: str,
        files: list[dict[str, Any]] | None = None,
        impact: dict[str, Any] | None = None,
        memory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        self.build_count += 1

        normalized_files = (
            self._normalize_files(
                files or []
            )
        )

        return {
            "context_id":
                str(
                    uuid4()
                ),

            "created_at":
                now_iso(),

            "task":
                task,

            "files":
                normalized_files,

            "impact":
                dict(
                    impact or {}
                ),

            "memory":
                dict(
                    memory or {}
                ),

            "context_size":
                self._estimate_size(
                    normalized_files,
                    impact,
                    memory,
                ),
        }

    def merge(
        self,
        contexts: list[dict[str, Any]],
    ) -> dict[str, Any]:

        files = []
        impact = {}
        memory = {}

        for item in contexts:

            files.extend(
                item.get(
                    "files",
                    [],
                )
            )

            impact.update(
                item.get(
                    "impact",
                    {},
                )
            )

            memory.update(
                item.get(
                    "memory",
                    {},
                )
            )

        return {
            "context_id":
                str(
                    uuid4()
                ),

            "files":
                self._normalize_files(
                    files
                ),

            "impact":
                impact,

            "memory":
                memory,
        }

    def _normalize_files(
        self,
        files: list[Any],
    ) -> list[Any]:

        result = []
        seen = set()

        for item in files:

            key = str(
                item
            )

            if key not in seen:

                seen.add(
                    key
                )

                result.append(
                    item
                )

        return result

    def _estimate_size(
        self,
        files: list[Any],
        impact: dict[str, Any] | None,
        memory: dict[str, Any] | None,
    ) -> int:

        return len(
            str(
                files
            )
        ) + len(
            str(
                impact or {}
            )
        ) + len(
            str(
                memory or {}
            )
        )

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "CodeContextBuilder",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "metrics": {
                "build":
                    self.build_count,
            },

            "capabilities": [
                "context_build",
                "context_merge",
            ],
        }

__all__ = [
    "CodeContextBuilder",
]
