from __future__ import annotations

from backend.application.api_contract.command.runtime_session_command import (
    RuntimeSessionCommand,
)

from backend.application.api_contract.request.runtime_session_request import (
    RuntimeSessionRequest,
)


class RuntimeSessionRequestAdapter:
    """
    Request contract to command contract adapter.
    """

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return True

    def convert(
        self,
        request: RuntimeSessionRequest,
    ) -> RuntimeSessionCommand:

        return RuntimeSessionCommand(
            name=request.command,
            arguments={
                "session_id": request.session_id,
                "payload": request.payload,
            },
        )

    def dump(
        self,
    ) -> dict:
        return {
            "name": "RuntimeSessionRequestAdapter",
            "version": self.VERSION,
            "ready": self.ready(),
        }
