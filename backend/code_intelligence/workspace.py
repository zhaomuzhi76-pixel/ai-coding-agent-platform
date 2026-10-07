from __future__ import annotations

from backend.code_intelligence.kernel.intelligence_kernel import (
    IntelligenceKernel,
)
from backend.code_intelligence.project_analysis_facade import (
    ProjectAnalysisFacade,
)
from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)


class CodeIntelligenceWorkspace(
    CodeIntelligenceWorkspaceProtocol,
):
    """
    Domain-owned workspace intelligence facade.

    Concrete kernel/facade assembly remains inside Code Intelligence.
    Upper layers consume only CodeIntelligenceWorkspaceProtocol.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        kernel: IntelligenceKernel,
        facade: ProjectAnalysisFacade,
    ) -> None:
        if not isinstance(kernel, IntelligenceKernel):
            raise TypeError(
                "kernel must IntelligenceKernel"
            )

        if not isinstance(
            facade,
            ProjectAnalysisFacade,
        ):
            raise TypeError(
                "facade must ProjectAnalysisFacade"
            )

        self.kernel = kernel
        self.facade = facade

        if not self.ready():
            raise RuntimeError(
                "code intelligence workspace unavailable"
            )

    def project_intelligence(self) -> dict[str, object]:
        return self.kernel.project_intelligence()

    def project_summary(self) -> dict[str, object]:
        return self.kernel.project_summary()

    def analyze_file(
        self,
        path: str,
    ) -> dict[str, object]:
        return self.kernel.analyze_file(path)

    def build_index(self) -> list[dict[str, object]]:
        return self.kernel.build_index()

    def analyze_project(self) -> dict[str, object]:
        return self.facade.analyze_project()

    def analyze_impact(
        self,
        *,
        file: str,
        symbol: str | None = None,
    ) -> dict[str, object]:
        return self.facade.analyze_impact(
            file=file,
            symbol=symbol,
        )

    def build_context(
        self,
        *,
        task: str,
    ) -> dict[str, object]:
        return self.facade.build_context(task=task)

    def ready(self) -> bool:
        return (
            self.kernel.ready()
            and self.facade.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "workspace": str(self.kernel.workspace),
            "ready": self.ready(),
            "kernel": type(self.kernel).__name__,
            "facade": type(self.facade).__name__,
        }


__all__ = [
    "CodeIntelligenceWorkspace",
]
