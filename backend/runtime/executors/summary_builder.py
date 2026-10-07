from __future__ import annotations

from typing import Any


class RuntimeSummaryBuilder:
    """
    Runtime execution summary builder.

    Responsibility:
        - normalize runtime execution summary

    Not Responsible:
        - result model
        - serialization
        - persistence
        - execution scheduling
    """

    VERSION = "6.0"

    RESPONSIBILITY = (
        "runtime_execution_summary_builder",
    )

    def build(
        self,
        result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        data = result or {}

        return {
            "status": data.get(
                "status",
                "unknown",
            ),
            "elapsed": data.get(
                "elapsed",
                0,
            ),
            "result": data.get(
                "result",
            ),
            "metadata": dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
        }

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": (
                "RuntimeSummaryBuilder"
            ),
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeSummaryBuilder",
]
