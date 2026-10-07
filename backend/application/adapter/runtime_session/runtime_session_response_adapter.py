from __future__ import annotations

from typing import Any

from backend.application.api_contract.response.runtime_session_response import (
    RuntimeSessionResponse,
)


class RuntimeSessionResponseAdapter:
    """
    Application result to response contract adapter.
    """

    VERSION = "1.0"

    def ready(
        self,
    ) -> bool:
        return True

    def convert(
        self,
        result: dict[str, Any],
    ) -> RuntimeSessionResponse:

        return RuntimeSessionResponse(
            status=result.get(
                "status",
                "success",
            ),
            data=result,
            error=result.get(
                "error"
            ),
        )

    def dump(
        self,
    ) -> dict:
        return {
            "name": "RuntimeSessionResponseAdapter",
            "version": self.VERSION,
            "ready": self.ready(),
        }
