from __future__ import annotations

from backend.core.agent.agent_request import (
    AgentRequest,
)


class RuntimeRequestValidator:
    """
    Runtime request contract validator.

    Responsibility:
        - validate the core-owned AgentRequest contract

    Not Responsible:
        - request construction
        - context creation
        - execution
        - planning
        - graph building
        - permission checking
        - persistence
    """

    VERSION = "5.0"

    RESPONSIBILITY = (
        "runtime_request_contract_validation",
    )

    def validate(
        self,
        request: AgentRequest,
    ) -> None:
        if not isinstance(
            request,
            AgentRequest,
        ):
            raise TypeError(
                "AgentRequest required"
            )

        if not request.ready():
            raise ValueError(
                "AgentRequest not ready"
            )

        if not isinstance(
            request.workspace,
            str,
        ):
            raise TypeError(
                "request.workspace must be str"
            )

        if not isinstance(
            request.model,
            str,
        ):
            raise TypeError(
                "request.model must be str"
            )

        if not isinstance(
            request.provider,
            str,
        ):
            raise TypeError(
                "request.provider must be str"
            )

        if not isinstance(
            request.stream,
            bool,
        ):
            raise TypeError(
                "request.stream must be bool"
            )

        if not isinstance(
            request.temperature,
            (int, float),
        ):
            raise TypeError(
                "request.temperature must be numeric"
            )

        if request.max_tokens is not None and not isinstance(
            request.max_tokens,
            int,
        ):
            raise TypeError(
                "request.max_tokens must be int or None"
            )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeRequestValidator",
]
