from __future__ import annotations

from backend.core.agent.agent_event import AgentEvent
from backend.core.events.contracts import EventProtocol
from backend.core.events.types import CoreEventType
from backend.runtime.events.event import RuntimeEvent


class RuntimeAgentEventAdapter:
    """
    Runtime representation adapter for core AgentEvent.

    Responsibility:
        - convert Core AgentEvent into RuntimeEvent
        - preserve semantic payload and execution identity
        - map agent events onto core-owned event semantics

    Not Responsible:
        - event dispatch
        - event persistence
        - event ownership
        - semantic event type definition
    """

    VERSION = "1.1"

    TYPE_MAPPING = {
        "kernel_start": CoreEventType.RUNTIME_START,
        "kernel_success": CoreEventType.RUNTIME_FINISH,
        "kernel_finish": CoreEventType.RUNTIME_FINISH,
        "kernel_failed": CoreEventType.RUNTIME_FAILED,
        "memory_write": CoreEventType.MEMORY_WRITE,
    }

    def to_runtime(
        self,
        event: AgentEvent,
    ) -> RuntimeEvent:
        if event is None:
            raise ValueError(
                "agent event required"
            )

        if not isinstance(
            event,
            EventProtocol,
        ):
            raise TypeError(
                "event must implement EventProtocol"
            )

        if not isinstance(
            event,
            AgentEvent,
        ):
            raise TypeError(
                "event must AgentEvent"
            )

        if not event.ready():
            raise ValueError(
                "agent event not ready"
            )

        runtime_type = self.TYPE_MAPPING.get(
            event.type
        )

        if runtime_type is None:
            raise ValueError(
                f"unsupported agent event type: {event.type}"
            )

        return RuntimeEvent.create(
            runtime_type,
            data=dict(
                event.payload
            ),
            source=(
                event.agent_name
                or "agent"
            ),
            metadata={
                "agent_event_type": event.type,
                "agent_status": event.status,
                "task_id": event.task_id,
                "execution_id": event.execution_id,
                "agent_name": event.agent_name,
            },
        )

    def ready(
        self,
    ) -> bool:
        return bool(
            self.TYPE_MAPPING
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "mapping_count": len(
                self.TYPE_MAPPING
            ),
        }


__all__ = [
    "RuntimeAgentEventAdapter",
]
