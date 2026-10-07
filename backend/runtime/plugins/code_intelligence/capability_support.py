from __future__ import annotations

from pathlib import Path
from typing import Callable

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceRequest,
)
from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)


WorkspaceResolver = Callable[
    [str],
    CodeIntelligenceWorkspaceProtocol,
]


class CodeIntelligenceCapabilitySupport:
    """
    Runtime support for workspace resolution and operation dispatch.
    """

    VERSION = "2.0"

    def __init__(
        self,
        workspace: CodeIntelligenceWorkspaceProtocol,
        resolver: WorkspaceResolver | None = None,
    ) -> None:
        if not isinstance(
            workspace,
            CodeIntelligenceWorkspaceProtocol,
        ):
            raise TypeError(
                "workspace must CodeIntelligenceWorkspaceProtocol"
            )

        self.workspace = workspace
        self.resolver = resolver

    def scope(
        self,
        workspace: str,
    ) -> CodeIntelligenceWorkspaceProtocol:
        normalized = str(
            Path(workspace)
            .expanduser()
            .resolve()
        )

        current = self._workspace_root(
            self.workspace
        )

        if normalized == current:
            return self.workspace

        if self.resolver is None:
            raise RuntimeError(
                "request workspace is outside "
                "the configured code intelligence scope"
            )

        resolved = self.resolver(
            normalized
        )

        if not resolved.ready():
            raise RuntimeError(
                "resolved code intelligence workspace unavailable"
            )

        return resolved

    @staticmethod
    def inspect(
        request: CodeIntelligenceRequest,
        workspace: CodeIntelligenceWorkspaceProtocol,
    ) -> list[object]:
        operation_value = request.metadata.get(
            "operation"
        )

        if operation_value is None:
            operation = (
                "file"
                if request.path
                else "summary"
            )
        else:
            operation = str(
                operation_value
            ).strip().lower()

        if operation == "project":
            return [
                workspace.project_intelligence()
            ]

        if operation == "summary":
            return [
                workspace.project_summary()
            ]

        if operation == "file":
            if not request.path:
                raise ValueError(
                    "path required for file inspection"
                )
            return [
                workspace.analyze_file(
                    request.path
                )
            ]

        if operation == "analysis":
            return [
                workspace.analyze_project()
            ]

        if operation == "impact":
            if not request.path:
                raise ValueError(
                    "path required for impact analysis"
                )
            return [
                workspace.analyze_impact(
                    file=request.path,
                    symbol=request.metadata.get(
                        "symbol"
                    ),
                )
            ]

        if operation == "context":
            return [
                workspace.build_context(
                    task=request.query
                )
            ]

        if operation == "index":
            return [
                {
                    "files": workspace.build_index()
                }
            ]

        raise ValueError(
            "unsupported code intelligence operation: "
            f"{operation}"
        )

    def ready(self) -> bool:
        return self.workspace.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "resolver": self.resolver is not None,
        }

    @staticmethod
    def _workspace_root(
        workspace: CodeIntelligenceWorkspaceProtocol,
    ) -> str:
        dump = workspace.dump()
        root = dump.get("workspace")

        if isinstance(root, str) and root.strip():
            return str(
                Path(root)
                .expanduser()
                .resolve()
            )

        raise RuntimeError(
            "code intelligence workspace root unavailable"
        )


__all__ = [
    "CodeIntelligenceCapabilitySupport",
]
