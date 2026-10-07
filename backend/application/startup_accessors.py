from __future__ import annotations

from typing import Any


class ApplicationStartupAccessors:
    """
    Public state projection helpers for ApplicationStartup.

    Owns:
        - application component accessors
        - lifecycle state accessors
        - runtime execution gateway projection

    Does not own:
        - component construction
        - component lifecycle
    """

    VERSION = "1.3"

    @staticmethod
    def registry(owner: Any) -> Any:
        return owner.registry

    @staticmethod
    def runtime(state: Any) -> Any:
        return state.runtime

    @staticmethod
    def agent_service(state: Any) -> Any:
        return state.agent_service


    @staticmethod
    def runtime_submission(state: Any) -> Any:
        return state.runtime_submission

    @staticmethod
    def execution_gateway(state: Any) -> Any:
        return state.runtime_execution_gateway

    @staticmethod
    def event_bus(state: Any) -> Any:
        runtime = state.runtime
        if runtime is None:
            raise RuntimeError(
                "runtime startup projection unavailable"
            )

        event_bus = getattr(
            runtime,
            "event_bus",
            None,
        )
        if event_bus is None:
            raise RuntimeError(
                "event bus startup projection unavailable"
            )

        return event_bus

    @staticmethod
    def capability_manager(state: Any) -> Any:
        return state.capability_manager

    @staticmethod
    def started(state: Any) -> bool:
        return bool(state.started)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ApplicationStartupAccessors",
]
