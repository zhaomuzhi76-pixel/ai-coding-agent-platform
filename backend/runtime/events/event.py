from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from backend.core.events.types import CoreEventType
from backend.utils.time import now_iso


@dataclass(slots=True)
class RuntimeEvent:
    """
    Runtime-owned event entity.

    Responsibility:
        - represent runtime event data
        - validate against the core semantic event contract
        - serialize runtime event data

    Not Responsible:
        - semantic event type definition
        - dispatch
        - persistence
        - transport
    """

    VERSION = "2.1"
    SCHEMA_VERSION = "runtime.event.v2"

    RESPONSIBILITY = (
        "runtime_event_entity",
    )

    type: str
    data: dict[str, Any] = field(
        default_factory=dict,
    )
    source: str = "runtime"
    node_id: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
    event_id: str = field(
        default_factory=lambda: uuid4().hex,
    )
    timestamp: str = field(
        default_factory=now_iso,
    )

    def ready(self) -> bool:
        return all(
            (
                isinstance(self.type, str),
                bool(self.type),
                CoreEventType.contains(self.type),
                isinstance(self.data, dict),
                isinstance(self.metadata, dict),
                isinstance(self.source, str),
                bool(self.timestamp),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.SCHEMA_VERSION,
            "event_id": self.event_id,
            "type": self.type,
            "node_id": self.node_id,
            "data": deepcopy(self.data),
            "metadata": deepcopy(self.metadata),
            "source": self.source,
            "timestamp": self.timestamp,
        }

    def dump(self) -> dict[str, Any]:
        result = self.to_dict()
        result.update(
            {
                "version": self.VERSION,
                "responsibility": self.RESPONSIBILITY,
            }
        )
        return result

    @classmethod
    def create(
        cls,
        event_type: str,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "RuntimeEvent":
        if not event_type:
            raise ValueError(
                "event_type required"
            )

        if not CoreEventType.contains(
            event_type
        ):
            raise ValueError(
                f"unsupported event type: {event_type}"
            )

        return cls(
            type=event_type,
            data=data or {},
            **kwargs,
        )


__all__ = [
    "RuntimeEvent",
]
