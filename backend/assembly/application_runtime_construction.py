from __future__ import annotations
from pathlib import Path
from backend.assembly.execution_dependency_port import (
    ExecutionDependencyAssemblyProtocol,
)
from backend.code_intelligence.composition import (
    CodeIntelligenceComposition,
)
from backend.code_intelligence.modification_factory import (
    ModificationFactory,
)
from backend.code_intelligence.analysis.analyzer import CodeAnalyzer
from backend.runtime.bootstrap.runtime_provider_factory import (
    RuntimeComponentProviderFactory,
)
from backend.workspace.contracts.runtime_contract import (
    WorkspaceRuntimeContract,
)
from backend.workspace.contracts.runtime_factory_contract import (
    WorkspaceRuntimeFactoryContract,
)
from backend.workspace.runtime.workspace_runtime_factory import (
    WorkspaceRuntimeFactory,
)
class ApplicationRuntimeConstruction:
    """
    Assembly-root Runtime construction.
    Owns:
        - Runtime infrastructure construction
        - Workspace construction
        - execution dependency injection
        - executor binding
    Does not own:
        - Application adapters
        - runtime execution algorithms
        - application orchestration
        - transport
    """
    VERSION = "3.0"
    def __init__(
        self,
        *,
        workspace_root: str,
        execution_dependency_assembly: (
            ExecutionDependencyAssemblyProtocol
        ),
        factory: RuntimeComponentProviderFactory | None = None,
        workspace_factory: (
            WorkspaceRuntimeFactoryContract | None
        ) = None,
    ) -> None:
        if (
            not isinstance(workspace_root, str)
            or not workspace_root.strip()
        ):
            raise ValueError("workspace root required")
        if not isinstance(
            execution_dependency_assembly,
            ExecutionDependencyAssemblyProtocol,
        ):
            raise TypeError(
                "execution dependency assembly contract required"
            )
        if not execution_dependency_assembly.ready():
            raise RuntimeError(
                "execution dependency assembly unavailable"
            )
        self.workspace_root = str(
            Path(workspace_root)
            .expanduser()
            .resolve()
        )
        self.factory = (
            factory
            if factory is not None
            else RuntimeComponentProviderFactory()
        )
        self.workspace_factory = (
            workspace_factory
            if workspace_factory is not None
            else WorkspaceRuntimeFactory()
        )
        self.execution_dependency_assembly = (
            execution_dependency_assembly
        )
        if not self.factory.ready():
            raise RuntimeError(
                "runtime provider factory unavailable"
            )
        if not isinstance(
            self.workspace_factory,
            WorkspaceRuntimeFactoryContract,
        ):
            raise TypeError(
                "workspace factory contract required"
            )
        if not self.workspace_factory.ready():
            raise RuntimeError(
                "workspace runtime factory unavailable"
            )
        self.workspace: WorkspaceRuntimeContract | None = None
    def create(self):
        code_intelligence_workspace = (
            CodeIntelligenceComposition(
                workspace=self.workspace_root,
            ).create()
        )
        code_modification_provider = (
            ModificationFactory().create_pipeline()
        )
        code_analyzer = CodeAnalyzer()
        runtime = self.factory.create(
            workspace_root=self.workspace_root,
            workspace_factory=self.workspace_factory,
            code_intelligence_workspace=code_intelligence_workspace,
            code_intelligence_resolver=lambda root: CodeIntelligenceComposition(
                workspace=root,
            ).create(),
            code_modification_provider=code_modification_provider,
            code_analyzer=code_analyzer,
        )
        workspace = self.workspace_factory.create(
            self.workspace_root
        )
        if not isinstance(
            workspace,
            WorkspaceRuntimeContract,
        ):
            close = getattr(workspace, "close", None)
            if callable(close):
                close()
            raise TypeError(
                "workspace runtime contract violation"
            )
        if not workspace.ready():
            workspace.close()
            raise RuntimeError(
                "workspace runtime unavailable"
            )
        self.workspace = workspace
        try:
            dependencies = (
                self.execution_dependency_assembly.create(
                    runtime=runtime,
                    workspace=workspace,
                )
            )
            ready = getattr(
                dependencies,
                "ready",
                None,
            )
            if not callable(ready) or not ready():
                raise RuntimeError(
                    "execution dependency bundle unavailable"
                )
            runtime.configure_executor(
                llm_provider=dependencies.llm_provider,
                tools=dependencies.tools,
                modification=dependencies.modification,
            )
            if not runtime.execution_ready():
                raise RuntimeError(
                    "runtime execution infrastructure unavailable"
                )
            return runtime
        except Exception:
            close = getattr(
                workspace,
                "close",
                None,
            )
            if callable(close):
                close()
            self.workspace = None
            raise
    def ready(self) -> bool:
        return (
            self.factory.ready()
            and self.workspace_factory.ready()
            and self.execution_dependency_assembly.ready()
        )
    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "workspace_root": self.workspace_root,
            "workspace_factory": type(
                self.workspace_factory
            ).__name__,
            "workspace": (
                type(self.workspace).__name__
                if self.workspace is not None
                else None
            ),
            "factory": type(self.factory).__name__,
            "execution_dependency_assembly": type(
                self.execution_dependency_assembly
            ).__name__,
            "ready": self.ready(),
        }
__all__ = [
    "ApplicationRuntimeConstruction",
]
