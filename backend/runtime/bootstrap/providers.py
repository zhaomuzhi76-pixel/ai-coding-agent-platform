from __future__ import annotations

from backend.runtime.application.runtime_application_provider import RuntimeApplicationProvider
from backend.runtime.bootstrap.component_builder import RuntimeComponentBuilder
from backend.runtime.bootstrap.executor_plugin_binder import RuntimeExecutorPluginBinder
from backend.runtime.bootstrap.plugin_provider import RuntimePluginProvider
from backend.runtime.bootstrap.runtime_component_bootstrap import RuntimeComponentBootstrap
from backend.runtime.bootstrap.runtime_plugin_access import RuntimePluginAccess
from backend.runtime.bootstrap.runtime_semantic_capability_access import RuntimeSemanticCapabilityAccess
from backend.runtime.bootstrap.tool_registrar import RuntimeBuiltinToolRegistrar
from backend.runtime.bootstrap.tool_runtime_provider import RuntimeToolRuntimeProvider
from backend.runtime.events.agent_event_bus import RuntimeAgentEventBus
from backend.runtime.plugin.capability import RuntimeCapability
from backend.workspace.contracts.runtime_factory_contract import WorkspaceRuntimeFactoryContract


class RuntimeComponentProvider:
    """Stable Runtime facade for Assembly/Application consumers."""

    VERSION = "20.0"

    def __init__(
        self,
        *,
        workspace_root: str,
        workspace_factory: WorkspaceRuntimeFactoryContract,
        code_intelligence_workspace,
        code_intelligence_resolver,
        code_modification_provider,
        code_analyzer,
    ) -> None:
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            raise ValueError("workspace root required")
        if not isinstance(workspace_factory, WorkspaceRuntimeFactoryContract):
            raise TypeError("workspace factory contract required")
        if not workspace_factory.ready():
            raise RuntimeError("workspace runtime factory unavailable")
        if not code_intelligence_workspace.ready():
            raise RuntimeError("code intelligence workspace unavailable")
        if not code_modification_provider.ready():
            raise RuntimeError("code modification provider unavailable")
        if not code_analyzer.ready():
            raise RuntimeError("code analyzer unavailable")

        self.workspace_root = workspace_root
        self.workspace_factory = workspace_factory
        self.tool_runtime_provider = None
        self.plugin_provider = None
        self.plugin_access = None
        self.semantic = None
        self.application_provider = None
        self.builder = None
        self.executor_binder = None
        self._tool_registrar = None
        self.event_bus = None
        self.intelligence_event_binder = None

        RuntimeComponentBootstrap().initialize(
            self,
            workspace_root=workspace_root,
            workspace_factory=workspace_factory,
            code_intelligence_workspace=code_intelligence_workspace,
            code_intelligence_resolver=code_intelligence_resolver,
            code_modification_provider=code_modification_provider,
            code_analyzer=code_analyzer,
        )

        self.plugin_access = RuntimePluginAccess(
            plugin_provider=self.plugin_provider,
        )
        self.semantic = RuntimeSemanticCapabilityAccess(
            plugin_provider=self.plugin_provider,
        )

        if not self.plugin_access.ready():
            raise RuntimeError("runtime plugin access unavailable")
        if not self.semantic.ready():
            raise RuntimeError("runtime semantic access unavailable")

    def create_tool_runtime(self, workspace: object):
        runtime = self.tool_runtime_provider.create(workspace)
        if not runtime.ready():
            raise RuntimeError("tool runtime unavailable")
        return runtime

    def create_execution_engine(self):
        engine = self.builder.create("execution.engine")
        if not engine.ready():
            raise RuntimeError(
                "runtime execution engine unavailable"
            )
        return engine

    def create_event_bus(self) -> RuntimeAgentEventBus:
        return self.event_bus


    def create_knowledge_middleware(self):
        return self.semantic.create_knowledge_middleware()

    def create_code_intelligence_capability(self):
        return self.semantic.create_code_intelligence_capability()

    def create_code_modification_provider(self):
        return self.semantic.create_code_modification_provider()

    def create_result_factory(self):
        return self.application_provider.create_result_factory()

    def create_runtime_flow(self, *, preparer, executor):
        flow = self.application_provider.create_flow(
            preparer=preparer,
            executor=executor,
        )
        if not flow.ready():
            raise RuntimeError(
                "runtime execution flow unavailable"
            )
        return flow


    def configure_executor(
        self,
        *,
        llm_provider,
        tools,
        modification,
    ):
        executor = self.executor_binder.bind(
            llm_provider=llm_provider,
            tools=tools,
            modification=modification,
        )
        if not self.executor_binder.ready():
            raise RuntimeError("runtime executor binder unavailable")
        return executor

    def register_capability(
        self,
        capability: RuntimeCapability,
        provider: object,
    ) -> None:
        self.plugin_access.register_capability(
            capability,
            provider,
        )

    def resolve_capability(
        self,
        capability: RuntimeCapability | str,
        version: str | None = None,
    ) -> object:
        return self.plugin_access.resolve_capability(capability, version)

    def create_component(self, capability: str) -> object:
        return self.builder.create(capability)

    def has_component(self, capability: str) -> bool:
        return self.builder.has(capability)

    def discover_plugins(self) -> list[object]:
        return self.plugin_access.discover_plugins()

    def load_plugins(self) -> list[object]:
        return self.plugin_access.load_plugins()

    def infrastructure_ready(self) -> bool:
        return all(
            (
                self.plugin_provider.ready(),
                self.plugin_access.ready(),
                self.semantic.ready(),
                self.tool_runtime_provider.ready(),
                self.event_bus.ready(),
                self.application_provider.ready(),
                self.builder.ready(),
            )
        )

    def execution_ready(self) -> bool:
        return self.infrastructure_ready() and self.executor_binder.ready()

    def ready(self) -> bool:
        return self.infrastructure_ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "workspace_root": self.workspace_root,
            "plugin_provider": self.plugin_provider.dump(),
            "plugin_access": self.plugin_access.dump(),
            "semantic": self.semantic.dump(),
            "tool_runtime_provider": self.tool_runtime_provider.dump(),
            "event_bus": self.event_bus.dump(),
            "application_provider": self.application_provider.dump(),
            "executor_binder": self.executor_binder.dump(),
            "builder": self.builder.dump(),
            "tool_registrar": self._tool_registrar.dump(),
            "infrastructure_ready": self.infrastructure_ready(),
            "execution_ready": self.execution_ready(),
            "ready": self.ready(),
        }


__all__ = ["RuntimeComponentProvider"]
