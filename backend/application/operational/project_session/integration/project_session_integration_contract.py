from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol
from backend.core.result import ExecutionResult


@runtime_checkable
class ProjectSessionIntegrationBridgeContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    """
    Session-gated Application integration bridge contract.

    Owns:
        - active-session admission
        - downstream delegation
        - session_id propagation

    Does not own:
        - session construction
        - session lifecycle mutation
        - project registry
        - Agent implementation
        - submission implementation
        - runtime implementation
        - transport
    """

    async def execute(
        self,
        request: object,
        session_id: str,
    ) -> ExecutionResult:
        ...


__all__ = [
    "ProjectSessionIntegrationBridgeContract",
]
