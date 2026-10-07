from __future__ import annotations

from typing import Any
from uuid import uuid4

from backend.utils.time import now_iso

class ModificationPlanner:
    """
    Code modification planning engine.

    Responsibility:
        - create modification plan
        - define affected files
        - build execution sequence

    Not Responsible:
        - code generation
        - patch creation
        - file writing
        - verification
        - rollback
        - repair
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "industrial_modification_planning"
    )

    def __init__(
        self,
    ) -> None:

        self.plan_count = 0

    def plan(
        self,
        *,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        self.plan_count += 1

        runtime = (
            context
            or {}
        )

        files = self._collect_files(
            runtime,
        )

        steps = self._build_steps(
            task,
            files,
        )

        return {
            "plan_id":
                str(
                    uuid4()
                ),

            "task":
                task,

            "created_at":
                now_iso(),

            "files":
                files,

            "steps":
                steps,

            "risk":
                self._risk(
                    len(files),
                ),
        }

    def _collect_files(
        self,
        context: dict[str, Any],
    ) -> list[str]:

        result = []

        for item in context.get(
            "files",
            [],
        ):

            if isinstance(
                item,
                str,
            ):

                result.append(
                    item
                )

            elif isinstance(
                item,
                dict,
            ):

                file = item.get(
                    "file",
                )

                if file:

                    result.append(
                        str(
                            file
                        )
                    )

        return list(
            dict.fromkeys(
                result
            )
        )

    def _build_steps(
        self,
        task: str,
        files: list[str],
    ) -> list[dict[str, Any]]:

        return [
            {
                "step_id":
                    str(
                        uuid4()
                    ),

                "action":
                    "modify",

                "file":
                    file,

                "reason":
                    task,
            }
            for file
            in files
        ]

    def _risk(
        self,
        count: int,
    ) -> str:

        if count == 0:
            return "unknown"

        if count <= 2:
            return "low"

        if count <= 5:
            return "medium"

        return "high"

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "ModificationPlanner",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "metrics": {
                "plans":
                    self.plan_count,
            },

            "capabilities": [
                "plan_creation",
                "step_generation",
                "risk_estimation",
            ],
        }

__all__ = [
    "ModificationPlanner",
]
