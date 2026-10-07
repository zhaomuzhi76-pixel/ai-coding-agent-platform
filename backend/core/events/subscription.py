from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from backend.core.contracts.value import (
    CoreValue,
)

from backend.core.events.contracts import (
    EventHandler,
)


@dataclass(
    frozen=True,
    slots=True,
)
class EventSubscription:
    """
    Canonical event subscription value.

    Owns:
        - subscription identity
        - event type binding
        - handler reference

    Does not own:
        - dispatch
        - handler execution
        - event storage
        - transport
    """

    event_type: str
    handler: EventHandler

    subscription_id: str = field(
        default_factory=lambda:
        f"sub_{uuid4().hex}",
        init=False,
    )

    def __post_init__(self) -> None:
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

        if not normalized:
            raise ValueError(
                "event type required"
            )

        object.__setattr__(
            self,
            "event_type",
            normalized,
        )

        if not callable(
            self.handler,
        ):
            raise TypeError(
                "event handler required"
            )

    def ready(
        self,
    ) -> bool:
        return bool(
            self.subscription_id
            and self.event_type
            and callable(self.handler)
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "subscription_id": self.subscription_id,
            "event_type": self.event_type,
            "handler": (
                getattr(
                    self.handler,
                    "__name__",
                    type(
                        self.handler
                    ).__name__,
                )
            ),
            "ready": self.ready(),
        }


__all__ = [
    "EventSubscription",
]
