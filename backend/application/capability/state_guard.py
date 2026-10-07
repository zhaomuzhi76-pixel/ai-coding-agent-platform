from __future__ import annotations

from backend.application.capability.lifecycle import (
    ApplicationCapabilityState,
)


class ApplicationCapabilityStateGuard:
    """
    Capability lifecycle state validation.

    Owns:
        - state validation

    Does not own:
        - lifecycle transition
    """

    VERSION = "1.0"

    @staticmethod
    def require_not_unloaded(
        state: ApplicationCapabilityState,
        name: str,
    ) -> None:
        if state is ApplicationCapabilityState.UNLOADED:
            raise RuntimeError(
                f"capability unloaded: {name}"
            )

    @staticmethod
    def require_enabled(
        state: ApplicationCapabilityState,
    ) -> None:
        if state is not ApplicationCapabilityState.ENABLED:
            raise RuntimeError(
                f"invalid capability state: {state.value}"
            )

    @staticmethod
    def require_disabled(
        state: ApplicationCapabilityState,
    ) -> None:
        if state is not ApplicationCapabilityState.DISABLED:
            raise RuntimeError(
                f"invalid capability state: {state.value}"
            )


__all__ = [
    "ApplicationCapabilityStateGuard",
]
