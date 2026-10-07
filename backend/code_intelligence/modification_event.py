from __future__ import annotations

from typing import Any

from backend.utils.time import now_iso

class ModificationEvent:
    """
    Modification lifecycle event model.

    Responsibility:
        - define modification event data
        - create lifecycle event payload

    Not Responsible:
        - event publishing
        - event subscription
        - event storage
        - websocket communication
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "code_modification_event_model"
    )

    TYPES = (
        "modification.started",
        "modification.planned",
        "modification.executed",
        "modification.verification_failed",
        "modification.rollback",
        "modification.completed",
    )

    def __init__(
        self,
        event_type: str,
        *,
        task: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:

        self.event_type = event_type
        self.task = task
        self.payload = (
            payload.copy()
            if payload
            else {}
        )

        self.created_at = now_iso()

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "event_version":
                self.VERSION,

            "event_type":
                self.event_type,

            "task":
                self.task,

            "payload":
                self.payload,

            "created_at":
                self.created_at,
        }

    @classmethod
    def create(
        cls,
        event_type: str,
        *,
        task: str = "",
        payload: dict[str, Any] | None = None,
    ) -> "ModificationEvent":

        if event_type not in cls.TYPES:
            raise ValueError(
                "unsupported_modification_event"
            )

        return cls(
            event_type,
            task=task,
            payload=payload,
        )

    def ready(
        self,
    ) -> bool:

        return (
            self.event_type
            in self.TYPES
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "ModificationEvent",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "event_type":
                self.event_type,

            "ready":
                self.ready(),
        }

__all__ = [
    "ModificationEvent",
]
