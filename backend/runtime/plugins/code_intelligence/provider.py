from __future__ import annotations

from pathlib import Path
from typing import Callable

from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)
from backend.runtime.plugins.code_intelligence.capability import (
    CodeIntelligenceCapability,
)

WorkspaceResolver = Callable[
    [str],
    CodeIntelligenceWorkspaceProtocol,
]


class CodeIntelligenceRuntimeCapabilityProvider:
    """
    Runtime provider for workspace-scoped code intelligence.

    Runtime consumes only Core workspace contracts.
    Concrete intelligence construction belongs to Assembly/Domain.
    """

    VERSION = "4.0"

    def __init__(
        self,
        *,
        workspace: CodeIntelligenceWorkspaceProtocol,
        resolver: WorkspaceResolver,
    ) -> None:
        if not isinstance(
            workspace,
            CodeIntelligenceWorkspaceProtocol,
        ):
            raise TypeError(
                "workspace must CodeIntelligenceWorkspaceProtocol"
            )

        if not callable(resolver):
            raise TypeError(
                "code intelligence workspace resolver required"
            )

        if not workspace.ready():
            raise RuntimeError(
                "code intelligence workspace unavailable"
            )

        self.workspace = workspace
        self.resolver = resolver
        self._scopes: dict[
            str,
            CodeIntelligenceWorkspaceProtocol,
        ] = {
            self._workspace_root(workspace): workspace,
        }

    def _resolve_scope(
        self,
        workspace: str,
    ) -> CodeIntelligenceWorkspaceProtocol:
        normalized = self._normalize_root(workspace)
        scope = self._scopes.get(normalized)

        if scope is None:
            scope = self.resolver(normalized)

            if not isinstance(
                scope,
                CodeIntelligenceWorkspaceProtocol,
            ):
                raise TypeError(
                    "resolved workspace must "
                    "CodeIntelligenceWorkspaceProtocol"
                )

            if not scope.ready():
                raise RuntimeError(
                    "resolved code intelligence workspace unavailable"
                )

            self._scopes[normalized] = scope

        return scope

    def create(
        self,
    ) -> CodeIntelligenceCapability:
        capability = CodeIntelligenceCapability(
            workspace=self.workspace,
            workspace_resolver=self._resolve_scope,
        )

        if not capability.ready():
            raise RuntimeError(
                "code intelligence capability unavailable"
            )

        return capability

    def ready(
        self,
    ) -> bool:
        return (
            self.workspace.ready()
            and callable(self.resolver)
            and all(
                scope.ready()
                for scope in self._scopes.values()
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "scope_count": len(self._scopes),
            "ready": self.ready(),
            "workspace": type(self.workspace).__name__,
        }

    @staticmethod
    def _workspace_root(
        workspace: CodeIntelligenceWorkspaceProtocol,
    ) -> str:
        dump = workspace.dump()
        root = dump.get("workspace")

        if isinstance(root, str) and root.strip():
            return CodeIntelligenceRuntimeCapabilityProvider._normalize_root(
                root
            )

        raise RuntimeError(
            "code intelligence workspace root unavailable"
        )

    @staticmethod
    def _normalize_root(
        workspace: str,
    ) -> str:
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError(
                "workspace root required"
            )

        return str(
            Path(workspace)
            .expanduser()
            .resolve()
        )


__all__ = [
    "CodeIntelligenceRuntimeCapabilityProvider",
    "WorkspaceResolver",
]
