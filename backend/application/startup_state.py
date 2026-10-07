from __future__ import annotations

from typing import Any


class ApplicationStartupState:
    """
    Mutable application startup state.

    Owns:
        - canonical startup component identity
        - startup context projection
        - runtime execution gateway identity

    Does not own:
        - component construction
        - lifecycle orchestration
        - component implementation
    """

    VERSION = "2.4"

    def __init__(self) -> None:
        self.runtime: Any = None
        self.agent_service: Any = None
        self.runtime_submission: Any = None
        self.runtime_execution_gateway: Any = None
        self.capability_manager: Any = None
        self.started = False
        self.context: dict[str, Any] = {}

    def commit(
        self,
        result: dict[str, Any],
    ) -> None:
        context = dict(result["context"])
        runtime_execution_gateway = context.get(
            "runtime_execution_gateway"
        )

        if runtime_execution_gateway is None:
            raise RuntimeError(
                "runtime execution gateway missing from startup context"
            )

        if not callable(
            getattr(runtime_execution_gateway, "ready", None)
        ):
            raise TypeError(
                "runtime execution gateway must expose ready()"
            )

        if not runtime_execution_gateway.ready():
            raise RuntimeError(
                "runtime execution gateway unavailable"
            )

        self.context = context
        self.capability_manager = result["manager"]
        self.runtime = result["runtime"]
        self.agent_service = result[
            "agent_service"
        ]
        self.runtime_submission = result[
            "runtime_submission"
        ]
        self.runtime_execution_gateway = (
            runtime_execution_gateway
        )

    def clear(self) -> None:
        self.context.clear()
        self.runtime_execution_gateway = None
        self.runtime_submission = None
        self.capability_manager = None
        self.agent_service = None
        self.runtime = None
        self.started = False

    def ready(self) -> bool:
        return not self.started or (
            self.runtime is not None
            and self.agent_service is not None
            and self.runtime_submission is not None
            and self.runtime_execution_gateway is not None
            and self.capability_manager is not None
        )

    def dump(self) -> dict[str, object]:
        wiring = (
            None
        )
        runtime_execution_gateway = (
            self.runtime_execution_gateway
        )

        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "started": self.started,
            "context_keys": tuple(
                sorted(
                    self.context.keys()
                )
            ),
            "runtime": (
                type(
                    self.runtime
                ).__name__
                if self.runtime is not None
                else None
            ),
            "capability_manager": (
                type(
                    self.capability_manager
                ).__name__
                if self.capability_manager is not None
                else None
            ),
            "runtime_execution_gateway": (
                type(
                    runtime_execution_gateway
                ).__name__
                if runtime_execution_gateway is not None
                else None
            ),
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationStartupState",
]
