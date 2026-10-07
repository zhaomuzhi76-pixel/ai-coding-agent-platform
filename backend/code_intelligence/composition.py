from __future__ import annotations

from pathlib import Path

from backend.code_intelligence.analysis.analyzer import (
    CodeAnalyzer,
)
from backend.code_intelligence.context_builder import (
    CodeContextBuilder,
)
from backend.code_intelligence.graph_provider import (
    GraphProvider,
)
from backend.code_intelligence.impact_analyzer import (
    ImpactAnalyzer,
)
from backend.code_intelligence.index.index_service import (
    CodeIndexService,
)
from backend.code_intelligence.kernel.intelligence_kernel import (
    IntelligenceKernel,
)
from backend.code_intelligence.project_analysis_facade import (
    ProjectAnalysisFacade,
)
from backend.code_intelligence.workspace import (
    CodeIntelligenceWorkspace,
)
from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)


class CodeIntelligenceComposition:
    """
    Sole construction owner for workspace-scoped code intelligence.

    Owns all concrete intelligence assembly.
    Consumers receive only CodeIntelligenceWorkspaceProtocol.
    """

    VERSION = "2.0"

    def __init__(
        self,
        *,
        workspace: str,
    ) -> None:
        if not isinstance(
            workspace,
            str,
        ) or not workspace.strip():
            raise ValueError(
                "workspace required"
            )

        self.workspace = str(
            Path(workspace)
            .expanduser()
            .resolve()
        )
        self._workspace: (
            CodeIntelligenceWorkspaceProtocol
            | None
        ) = None

    def create(
        self,
    ) -> CodeIntelligenceWorkspaceProtocol:
        if self._workspace is not None:
            return self._workspace

        index = CodeIndexService(
            self.workspace
        )
        analyzer = CodeAnalyzer()
        graph = GraphProvider()

        kernel = IntelligenceKernel(
            workspace=self.workspace,
            index_service=index,
            analyzer=analyzer,
            graph_provider=graph,
        )

        facade = ProjectAnalysisFacade(
            root_path=self.workspace,
            index_service=index,
            context_builder=CodeContextBuilder(),
            impact_analyzer=ImpactAnalyzer(),
            graph_provider=graph,
        )

        workspace = CodeIntelligenceWorkspace(
            kernel=kernel,
            facade=facade,
        )

        if not workspace.ready():
            raise RuntimeError(
                "code intelligence composition unavailable"
            )

        self._workspace = workspace
        return workspace

    def ready(self) -> bool:
        return (
            self._workspace is not None
            and self._workspace.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "workspace": self.workspace,
            "ready": self.ready(),
            "implementation": (
                type(self._workspace).__name__
                if self._workspace is not None
                else None
            ),
        }


__all__ = [
    "CodeIntelligenceComposition",
]
