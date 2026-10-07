from __future__ import annotations

from backend.application.api_contract.event.runtime_session_event import (
    RuntimeSessionEvent,
)


class RuntimeSessionEventAdapter:
    """
    Runtime session event adapter.
    """

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return True

    def validate(
        self,
        event: RuntimeSessionEvent,
    ) -> bool:

        return bool(
            event.ready()
        )

    def dump(
        self,
    ) -> dict:

        return {
            "name": "RuntimeSessionEventAdapter",
            "version": self.VERSION,
            "ready": self.ready(),
        }
