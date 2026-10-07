from __future__ import annotations

from enum import StrEnum


class CoreErrorCode(StrEnum):
    """
    Canonical framework error codes.

    Ownership:
        - define stable machine-readable error identity

    Not Responsible:
        - exception transport
        - websocket formatting
        - runtime execution
        - application business logic
    """

    VALIDATION = "validation_error"
    INVALID_STATE = "invalid_state"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    TIMEOUT = "timeout"
    EXECUTION = "execution_error"
    INTERNAL = "internal_error"


__all__ = [
    "CoreErrorCode",
]
