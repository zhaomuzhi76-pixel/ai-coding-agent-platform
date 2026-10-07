from __future__ import annotations

from backend.application.api_contract.command.runtime_session_command import (
    RuntimeSessionCommand,
)


class RuntimeSessionCommandAdapter:
    """
    Command contract validator and adapter.
    """

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return True

    def validate(
        self,
        command: RuntimeSessionCommand,
    ) -> bool:

        return bool(
            command.ready()
        )

    def dump(
        self,
    ) -> dict:
        return {
            "name": "RuntimeSessionCommandAdapter",
            "version": self.VERSION,
            "ready": self.ready(),
        }
