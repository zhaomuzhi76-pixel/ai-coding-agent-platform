from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.code_intelligence.analysis_port import (
    CodeAnalyzerProtocol,
)
from backend.core.tools.result_contract import ToolResultProtocol
from backend.workspace.contracts.index_contract import WorkspaceIndexContract
from backend.workspace.contracts.operation_contract import (
    WorkspaceOperationContract,
)
from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)


@runtime_checkable
class TerminalGuardProtocol(Protocol):
    def validate(self, command: str, workspace: str) -> None:
        ...

    def ready(self) -> bool:
        ...


__all__ = [
    "CodeAnalyzerProtocol",
    "TerminalGuardProtocol",
    "WorkspaceIndexContract",
    "WorkspaceOperationContract",
    "WorkspaceRuntimeContract",
    "ToolResultProtocol",
]
