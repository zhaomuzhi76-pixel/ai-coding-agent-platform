from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.core.contracts.value import (
    CoreValue,
    is_core_value,
)
from backend.core.events.contracts import (
    EventProtocol,
)
from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)


@dataclass(slots=True)
class AgentEvent(
    EventProtocol,
    ReadyProtocol,
    DumpableProtocol,
):
    """
    Core-owned agent semantic event contract.

    Responsibility:
        - represent one agent-domain event
        - carry stable event payload
        - expose execution identity metadata
        - expose readiness
        - expose serializable snapshot

    Not Responsible:
        - event dispatch
        - runtime event transport
        - runtime event representation
        - planning
        - execution
        - persistence
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "agent_domain_event_contract",
    )

    type: str

    payload: dict[str, CoreValue] = field(
        default_factory=dict,
    )

    task_id: str = ""
    execution_id: str = ""
    agent_name: str = ""
    status: str = "created"

    timestamp: str = field(
        default_factory=lambda: datetime.now(
            ZoneInfo("Asia/Shanghai")
        ).isoformat()
    )

    def complete(
        self,
        status: str,
    ) -> None:
        if not isinstance(
            status,
            str,
        ) or not status.strip():
            raise ValueError(
                "event status required"
            )

        self.status = status

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.type,
                str,
            )
            and bool(
                self.type.strip()
            )
            and isinstance(
                self.payload,
                dict,
            )
            and all(
                isinstance(key, str)
                and is_core_value(value)
                for key, value in self.payload.items()
            )
            and isinstance(
                self.status,
                str,
            )
            and bool(
                self.status.strip()
            )
            and bool(
                self.timestamp
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": list(self.RESPONSIBILITY),
            "type": self.type,
            "payload": dict(self.payload),
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "timestamp": self.timestamp,
        }


__all__ = [
    "AgentEvent",
]
