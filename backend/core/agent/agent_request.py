from __future__ import annotations

from dataclasses import dataclass, field

from backend.core.contracts.value import (
    CoreValue,
    is_core_value,
)
from backend.core.execution.execution_request_protocol import (
    ExecutionRequestProtocol,
)
from backend.core.protocols.dumpable import (
    DumpableProtocol,
)
from backend.core.protocols.ready import (
    ReadyProtocol,
)


@dataclass(slots=True)
class AgentRequest(
    ExecutionRequestProtocol,
    ReadyProtocol,
    DumpableProtocol,
):
    """
    Core-owned agent execution request contract.

    Responsibility:
        - represent one agent execution request
        - carry stable request metadata
        - expose readiness
        - expose serializable snapshot

    Not Responsible:
        - agent execution
        - planning
        - runtime execution
        - transport
        - persistence
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "agent_request_contract",
    )

    message: str
    provider: str = "ollama"
    model: str = "locooperator-4b-8k"
    base_url: str = ""
    api_key: str = ""
    stream: bool = False
    temperature: float = 0.2
    max_tokens: int | None = None
    workspace: str = "."
    session_id: str = ""
    user_id: str = ""
    metadata: dict[str, CoreValue] = field(
        default_factory=dict,
    )

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(
                self.message,
                str,
            )
            and bool(
                self.message.strip()
            )
            and all(
                isinstance(key, str)
                and is_core_value(value)
                for key, value in self.metadata.items()
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": list(
                self.RESPONSIBILITY
            ),
            "message": self.message,
            "provider": self.provider,
            "model": self.model,
            "workspace": self.workspace,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "stream": self.stream,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "AgentRequest",
]
