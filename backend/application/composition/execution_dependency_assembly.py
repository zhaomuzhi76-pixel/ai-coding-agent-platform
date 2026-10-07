from __future__ import annotations

from backend.application.capability.code_modification_proposal_adapter import (
    CodeModificationProposalAdapter,
)
from backend.application.composition.execution_dependency_bundle import (
    ExecutionDependencyBundle,
)
from backend.application.composition.provider_factory import (
    ApplicationProviderCompositionFactory,
)
from backend.application.composition.tool_runtime_port import (
    ApplicationToolRuntimeProtocol,
)
from backend.application.modules.runtime_code_modification_adapter_factory import (
    RuntimeCodeModificationAdapterFactory,
)
from backend.application.modules.runtime_code_modification_execution_provider import (
    RuntimeCodeModificationExecutionProvider,
)
from backend.application.modules.runtime_llm_provider_adapter_factory import (
    RuntimeLLMProviderAdapterFactory,
)
from backend.application.provider_gateway.contracts import (
    ApplicationProviderRuntimeProtocol,
)
from backend.application.provider_gateway.model_router import ModelRouter
from backend.agent.orchestration import CodeEditOrchestrator
from backend.runtime.executors.runtime_dependencies import (
    set_runtime_deps,
)


class ApplicationExecutionDependencyAssembly:
    """
    Application 执行依赖装配。

    Owns:
        - provider gateway 暴露
        - provider adapter 构造
        - tool runtime 获取
        - modification proposal/pipeline 组装
        - 全局 runtime 依赖注册（供 fix_error 使用）

    Does not own:
        - Runtime execution algorithms
        - patch 实现
        - 验证
    """

    VERSION = "4.0"

    def __init__(
        self,
        *,
        provider_runtime: ApplicationProviderRuntimeProtocol,
    ) -> None:
        if not isinstance(
            provider_runtime,
            ApplicationProviderRuntimeProtocol,
        ):
            raise TypeError("provider runtime contract required")
        if not provider_runtime.ready():
            raise RuntimeError("provider runtime unavailable")

        self.provider_runtime = provider_runtime
        self.proposal_capability = None

    def bind_code_modification_proposal(
        self,
        proposal_capability: CodeModificationProposalAdapter,
    ) -> None:
        if not isinstance(
            proposal_capability,
            CodeModificationProposalAdapter,
        ):
            raise TypeError("proposal adapter required")
        if not proposal_capability.ready():
            raise RuntimeError("proposal unavailable")
        self.proposal_capability = proposal_capability

    def create(self, *, runtime, workspace) -> ExecutionDependencyBundle:
        if self.proposal_capability is None:
            raise RuntimeError("proposal must be bound")

        provider_gateway = (
            ApplicationProviderCompositionFactory()
            .create(runtime=self.provider_runtime)
            .create()
        )

        llm_provider = (
            RuntimeLLMProviderAdapterFactory()
            .create(provider=provider_gateway)
        )

        if workspace is None:
            raise ValueError("workspace runtime required")

        tools = runtime.create_tool_runtime(workspace=workspace)
        if not isinstance(tools, ApplicationToolRuntimeProtocol):
            raise TypeError("tool runtime contract required")

        pipeline = runtime.create_code_modification_provider()

        _router = ModelRouter()
        _orchestrator = CodeEditOrchestrator()

        modification_provider = (
            RuntimeCodeModificationExecutionProvider(
                proposal=self.proposal_capability,
                pipeline=pipeline,
                gateway=provider_gateway,
                router=_router,
                orchestrator=_orchestrator,
            )
        )

        # ★ 注册全局依赖，供 fix_error executor 使用
        set_runtime_deps(
            gateway=provider_gateway,
            router=_router,
            orchestrator=_orchestrator,
        )

        modification = (
            RuntimeCodeModificationAdapterFactory()
            .create(provider=modification_provider)
        )

        bundle = ExecutionDependencyBundle(
            llm_provider=llm_provider,
            tools=tools,
            modification=modification,
        )

        if not bundle.ready():
            raise RuntimeError("execution dependency bundle unavailable")

        return bundle

    def ready(self) -> bool:
        return bool(
            isinstance(
                self.provider_runtime,
                ApplicationProviderRuntimeProtocol,
            )
            and self.provider_runtime.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "proposal_bound": (
                self.proposal_capability is not None
            ),
            "provider_runtime": type(
                self.provider_runtime
            ).__name__,
        }


__all__ = [
    "ApplicationExecutionDependencyAssembly",
    "ExecutionDependencyBundle",
]
