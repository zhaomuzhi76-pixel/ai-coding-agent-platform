from __future__ import annotations

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceCapabilityProtocol,
    CodeIntelligenceRequest,
    CodeIntelligenceResult,
)
from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)
from backend.runtime.plugins.code_intelligence.capability_support import (
    CodeIntelligenceCapabilitySupport,
    WorkspaceResolver,
)
from backend.runtime.plugins.code_intelligence.finding import (
    RuntimeCodeIntelligenceFinding,
)


class CodeIntelligenceCapability(
    CodeIntelligenceCapabilityProtocol,
):
    """
    Runtime code-intelligence capability.

    Runtime consumes only the Core workspace intelligence port.
    """

    VERSION = "3.0"

    def __init__(
        self,
        *,
        workspace: CodeIntelligenceWorkspaceProtocol,
        workspace_resolver: WorkspaceResolver | None = None,
    ) -> None:
        if not isinstance(
            workspace,
            CodeIntelligenceWorkspaceProtocol,
        ):
            raise TypeError(
                "workspace must CodeIntelligenceWorkspaceProtocol"
            )

        self.workspace = workspace
        self.support = CodeIntelligenceCapabilitySupport(
            workspace=workspace,
            resolver=workspace_resolver,
        )
        self.inspect_count = 0

    async def inspect(
        self,
        request: CodeIntelligenceRequest,
    ) -> CodeIntelligenceResult:
        self._validate_request(request)

        workspace = self.support.scope(
            request.workspace
        )

        findings = self.support.inspect(
            request,
            workspace,
        )

        normalized = [
            item
            if isinstance(
                item,
                RuntimeCodeIntelligenceFinding,
            )
            else RuntimeCodeIntelligenceFinding(item)
            for item in findings
        ]

        self.inspect_count += 1

        return CodeIntelligenceResult(
            findings=tuple(normalized),
            metadata={
                "workspace": request.workspace,
                "path": request.path,
                "operation": (
                    request.metadata["operation"]
                    if "operation" in request.metadata
                    else (
                        "file"
                        if request.path
                        else "summary"
                    )
                ),
                "provider": type(self).__name__,
            },
        )

    def ready(self) -> bool:
        return self.support.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "inspect_count": self.inspect_count,
            "workspace": type(
                self.workspace
            ).__name__,
            "support": self.support.dump(),
        }

    @staticmethod
    def _validate_request(
        request: CodeIntelligenceRequest,
    ) -> None:
        if not isinstance(
            request,
            CodeIntelligenceRequest,
        ):
            raise TypeError(
                "request must CodeIntelligenceRequest"
            )

        if not request.ready():
            raise ValueError(
                "code intelligence request not ready"
            )


__all__ = [
    "CodeIntelligenceCapability",
]
