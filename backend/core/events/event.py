from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

from backend.core.contracts.timestamp import (
    now_timestamp,
)

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.events.contracts import (
    EventPayload,
)

from backend.core.events.types import (
    CoreEventType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class CoreEvent:
    """
    Canonical core event value object.

    Owns:
        - event identity
        - event semantic type
        - event timestamp
        - immutable payload snapshot

    Does not own:
        - event dispatch
        - subscriptions
        - transport
        - persistence
        - business execution
    """

    VERSION = "1.0"

    event_type: str

    payload: Mapping[
        str,
        CoreValue,
    ] = field(
        default_factory=dict,
    )

    event_id: str = field(
        default_factory=lambda:
        f"evt_{uuid4().hex}",
        init=False,
    )

    created_at: str = field(
        default_factory=now_timestamp,
        init=False,
    )

    def __post_init__(
        self,
    ) -> None:

        if not isinstance(
            self.event_type,
            str,
        ):
            raise TypeError(
                "event type must str"
            )

        normalized = (
            self.event_type.strip()
        )

        if not CoreEventType.contains(
            normalized,
        ):
            raise ValueError(
                f"unsupported event type: {normalized}"
            )

        object.__setattr__(
            self,
            "event_type",
            normalized,
        )

        if not isinstance(
            self.payload,
            Mapping,
        ):
            raise TypeError(
                "event payload must mapping"
            )

        object.__setattr__(
            self,
            "payload",
            MappingProxyType(
                dict(
                    self.payload
                )
            ),
        )

    @property
    def type(
        self,
    ) -> str:
        return self.event_type

    def ready(
        self,
    ) -> bool:
        return bool(
            self.event_id
            and self.event_type
            and self.created_at
            and CoreEventType.contains(
                self.event_type
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "event_id": self.event_id,
            "type": self.event_type,
            "created_at": self.created_at,
            "payload": dict(
                self.payload
            ),
            "ready": self.ready(),
        }


__all__ = [
    "CoreEvent",
]
