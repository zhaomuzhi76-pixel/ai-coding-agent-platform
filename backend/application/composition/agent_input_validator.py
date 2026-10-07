from __future__ import annotations

from typing import Any


class ApplicationAgentInputValidator:
    """
    Validate dependencies required by Agent Composition.

    Responsibility:
        - validate runtime application contract
        - validate runtime provider contract

    Not Responsible:
        - dependency construction
        - Agent construction
        - runtime execution
        - service construction
    """

    VERSION = "2.0"
    RESPONSIBILITY = (
        "application_agent_composition_input_validation",
    )

    def validate(
        self,
        *,

        runtime: Any,
    ) -> None:
        self._validate_runtime(
            runtime
        )

    @staticmethod
    def _validate_runtime(
        runtime: Any,
    ) -> None:
        if runtime is None:
            raise ValueError(
                "runtime component provider required"
            )

        required = (
            "create_event_bus",
        )

        for method in required:
            if not callable(
                getattr(runtime, method, None)
            ):
                raise TypeError(
                    f"runtime {method} factory unavailable"
                )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationAgentInputValidator",
]
