from __future__ import annotations

from backend.core.contracts.value import CoreValue
from backend.core.events.contracts import (
    EventTypeRegistryProtocol,
)


class CoreEventType(
    EventTypeRegistryProtocol,
):
    """
    Core-owned semantic event type registry.

    Owns:
        - stable event semantic identities
        - canonical event type membership

    Does not own:
        - event dispatch
        - event storage
        - transport
        - persistence
        - business execution
    """

    VERSION = "1.0"

    RUNTIME_START = "runtime_start"
    RUNTIME_FINISH = "runtime_finish"
    RUNTIME_FAILED = "runtime_failed"

    AGENT_READY = "agent_ready"

    NODE_START = "node_start"
    NODE_FINISH = "node_finish"
    NODE_FAILED = "node_failed"

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    MEMORY_WRITE = "memory_write"

    ERROR = "error"
    PENDING_EDIT = "pending_edit"

    _ALL = (
        RUNTIME_START,
        RUNTIME_FINISH,
        RUNTIME_FAILED,
        AGENT_READY,
        NODE_START,
        NODE_FINISH,
        NODE_FAILED,
        TOOL_CALL,
        TOOL_RESULT,
        MEMORY_WRITE,
        ERROR,
        PENDING_EDIT,
    )

    @classmethod
    def all(
        cls,
    ) -> tuple[str, ...]:
        return cls._ALL

    @classmethod
    def contains(
        cls,
        event_type: str,
    ) -> bool:
        return (
            isinstance(
                event_type,
                str,
            )
            and event_type in cls._ALL
        )

    @classmethod
    def ready(
        cls,
    ) -> bool:
        return bool(
            cls._ALL
        )

    @classmethod
    def dump(
        cls,
    ) -> dict[str, CoreValue]:
        return {
            "name": cls.__name__,
            "version": cls.VERSION,
            "ready": cls.ready(),
            "count": len(cls._ALL),
            "types": cls._ALL,
        }


__all__ = [
    "CoreEventType",
]
