from __future__ import annotations

from backend.core.code_intelligence.analysis_port import CodeAnalyzerProtocol
from backend.core.code_intelligence.workspace_port import CodeIntelligenceWorkspaceProtocol
from backend.core.execution.code_modification_contract import CodeModificationProviderProtocol
from backend.runtime.application.runtime_application_provider import RuntimeApplicationProvider
from backend.runtime.bootstrap.component_builder import RuntimeComponentBuilder
from backend.runtime.bootstrap.executor_plugin_binder import RuntimeExecutorPluginBinder
from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.bootstrap.intelligence_event_binder import IntelligenceEventBinder
from backend.runtime.bootstrap.plugin_provider import RuntimePluginProvider
from backend.runtime.bootstrap.tool_registrar import RuntimeBuiltinToolRegistrar
from backend.runtime.bootstrap.tool_runtime_provider import RuntimeToolRuntimeProvider
from backend.runtime.events.agent_event_bus import RuntimeAgentEventBus
from backend.workspace.contracts.runtime_factory_contract import WorkspaceRuntimeFactoryContract


class RuntimeComponentBootstrap:
    """
    Runtime infrastructure bootstrap boundary.

    Owns:
        - builtin runtime plugin registration
        - runtime infrastructure construction
        - event bridge construction
        - intelligence event composition

    Does not own:
        - workspace construction
        - application dependency assembly
        - executor dependency sourcing
        - application composition
        - runtime execution
    """

    VERSION = "2.0"

    def initialize(
        self,
        provider,
        *,
        workspace_root: str,
        workspace_factory: WorkspaceRuntimeFactoryContract,
        code_intelligence_workspace: (
            CodeIntelligenceWorkspaceProtocol
        ),
        code_intelligence_resolver,
        code_modification_provider: (
            CodeModificationProviderProtocol
        ),
        code_analyzer: CodeAnalyzerProtocol,
    ) -> None:
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            raise ValueError(
                "workspace root required"
            )
        if not isinstance(
            code_intelligence_workspace,
            CodeIntelligenceWorkspaceProtocol,
        ):
            raise TypeError(
                "code intelligence workspace contract required"
            )
        if not isinstance(
            code_modification_provider,
            CodeModificationProviderProtocol,
        ):
            raise TypeError(
                "code modification provider contract required"
            )
        if not isinstance(
            code_analyzer,
            CodeAnalyzerProtocol,
        ):
            raise TypeError(
                "code analyzer contract required"
            )

        provider.code_intelligence_workspace = (
            code_intelligence_workspace
        )
        provider.code_intelligence_resolver = (
            code_intelligence_resolver
        )
        provider.code_modification_provider = (
            code_modification_provider
        )
        provider.code_analyzer = code_analyzer

        provider._tool_registrar = (
            RuntimeBuiltinToolRegistrar(
                code_analyzer=code_analyzer,
            )
        )

        provider.tool_runtime_provider = (
            RuntimeToolRuntimeProvider(
                registrar=provider._tool_registrar,
                workspace_factory=workspace_factory,
            )
        )

        provider.plugin_provider = (
            RuntimePluginProvider(
                provider.tool_runtime_provider,
                workspace_root=workspace_root,
                code_intelligence_workspace=code_intelligence_workspace,
                code_intelligence_resolver=code_intelligence_resolver,
                code_modification_provider=code_modification_provider,
                code_analyzer=code_analyzer,
            )
        )

        registry = (
            provider.plugin_provider.capability_registry
        )

        provider.application_provider = (
            RuntimeApplicationProvider(
                capability_registry=registry
            )
        )


        provider.builder = RuntimeComponentBuilder(
            capability_registry=registry
        )

        provider.executor_binder = (
            RuntimeExecutorPluginBinder(
                provider.plugin_provider,
                tool_runtime_provider=(
                    provider.tool_runtime_provider
                ),
            )
        )

        provider.plugin_provider.register_builtins(
            code_intelligence_workspace=(
                provider.code_intelligence_workspace
            ),
            code_intelligence_resolver=(
                provider.code_intelligence_resolver
            ),
            code_modification_provider=(
                provider.code_modification_provider
            ),
            code_analyzer=provider.code_analyzer,
        )
        self._bind_event_bus(provider)
        self._bind_intelligence_events(provider)

    @staticmethod
    def _bind_event_bus(
        provider,
    ) -> None:
        runtime_event_bus = (
            provider.plugin_provider.resolve_capability(
                "events.bus"
            )
        )

        provider.event_bus = RuntimeAgentEventBus(
            runtime_bus=runtime_event_bus
        )

        provider.plugin_provider.register_capability(
            RuntimeCapability(
                category="events",
                name="agent_bus",
                version="1.0",
            ),
            provider.event_bus,
        )

    @staticmethod
    def _bind_intelligence_events(
        provider,
    ) -> None:
        binder = IntelligenceEventBinder(
            capability_registry=(
                provider.plugin_provider.capability_registry
            ),
            event_bus=provider.event_bus,
        )

        binder.bind()
        provider.intelligence_event_binder = binder

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeComponentBootstrap",
]
