from __future__ import annotations

from typing import Any

from backend.api.ws_request_values import (
    bool_value,
    float_value,
    metadata_value,
    optional_int,
    string_value,
)
from backend.core.agent.agent_request import (
    AgentRequest,
)


class ProjectSessionAgentRequestFactory:
    """
    HTTP project-session payload to AgentRequest boundary.

    Owns:
        - request payload validation
        - HTTP value normalization
        - AgentRequest construction
        - session-id injection

    Does not own:
        - session admission
        - runtime execution
        - submission execution
        - transport routing
    """

    VERSION = "1.0"

    def create(
        self,
        payload: dict[str, Any],
        session_id: str,
    ) -> AgentRequest:
        self._validate_payload(payload)
        self._validate_session(session_id)

        request = AgentRequest(
            message=string_value(
                payload,
                "message",
                "",
            ),
            provider=string_value(
                payload,
                "provider",
                "ollama",
            ),
            model=string_value(
                payload,
                "model",
                "locooperator-4b-8k",
            ),
            base_url=string_value(
                payload,
                "base_url",
                "",
            ),
            api_key=string_value(
                payload,
                "api_key",
                "",
            ),
            stream=bool_value(
                payload,
                "stream",
                False,
            ),
            temperature=float_value(
                payload,
                "temperature",
                0.2,
            ),
            max_tokens=optional_int(
                payload,
                "max_tokens",
            ),
            workspace=string_value(
                payload,
                "workspace",
                ".",
            ),
            session_id=session_id,
            user_id=string_value(
                payload,
                "user_id",
                "",
            ),
            metadata=metadata_value(
                payload
            ),
        )

        if not request.ready():
            raise ValueError(
                "agent request not ready"
            )

        return request

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _validate_payload(
        payload: object,
    ) -> None:
        if not isinstance(
            payload,
            dict,
        ):
            raise TypeError(
                "project session request must dict"
            )

    @staticmethod
    def _validate_session(
        session_id: object,
    ) -> None:
        if not isinstance(
            session_id,
            str,
        ) or not session_id.strip():
            raise ValueError(
                "session id required"
            )


__all__ = [
    "ProjectSessionAgentRequestFactory",
]
