from __future__ import annotations

from backend.core.code_intelligence.analysis_port import CodeAnalyzerProtocol
from backend.core.code_intelligence.workspace_port import CodeIntelligenceWorkspaceProtocol
from backend.core.execution.code_modification_contract import CodeModificationProviderProtocol
from pathlib import Path
from backend.core.code_intelligence.workspace_port import CodeIntelligenceWorkspaceProtocol
from backend.runtime.bootstrap.builtin_plugin_registry import builtin_plugins
from backend.runtime.bootstrap.plugin_provider_snapshot import build_plugin_provider_snapshot
from backend.runtime.bootstrap.tool_runtime_provider import RuntimeToolRuntimeProvider
from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.plugin.capability_registry import RuntimeCapabilityRegistry
from backend.runtime.plugin.controller import RuntimePluginController
from backend.runtime.plugin.discovery import RuntimePluginDiscovery
from backend.runtime.plugin.factory import RuntimeComponentFactory
from backend.runtime.plugin.loader import RuntimePluginLoader
from backend.runtime.plugin.plugin_action import RuntimePluginActionRegistry
from backend.runtime.plugin.plugin_lifecycle import RuntimePluginLifecycle
from backend.runtime.plugin.plugin_manager import RuntimePluginManager
from backend.runtime.plugin.operations import RuntimePluginOperations
from backend.runtime.plugin.registry import RuntimePluginRegistry
class RuntimePluginProvider:
    """
    Runtime plugin infrastructure composition root.
    Responsibility:
        - own plugin registry infrastructure
        - register builtin plugins
        - expose plugin and capability resolution
    """
    VERSION = "3.8"
    def __init__(
        self,
        tool_runtime_provider: RuntimeToolRuntimeProvider,
        *,
        workspace_root: str,
        code_intelligence_workspace: CodeIntelligenceWorkspaceProtocol,
        code_intelligence_resolver,
        code_modification_provider: CodeModificationProviderProtocol,
        code_analyzer: CodeAnalyzerProtocol,
    ) -> None:
        if not isinstance(
            tool_runtime_provider,
            RuntimeToolRuntimeProvider,
        ):
            raise TypeError(
                "tool runtime provider must "
                "RuntimeToolRuntimeProvider"
            )
        if not isinstance(workspace_root, str) or not workspace_root.strip():
            raise ValueError(
                "workspace root required"
            )
        self.tool_runtime_provider = tool_runtime_provider
        self.workspace_root = workspace_root
        self.code_modification_provider = code_modification_provider
        self.code_analyzer = code_analyzer
        self.code_intelligence_workspace = code_intelligence_workspace
        self.code_intelligence_resolver = code_intelligence_resolver
        self.registry = RuntimePluginRegistry()
        self.capability_registry = RuntimeCapabilityRegistry()
        self._manager = self._create_manager()
        self.factory = RuntimeComponentFactory(
            self.registry
        )
        self._builtin_registered = False
    def _create_manager(
        self,
    ) -> RuntimePluginManager:
        lifecycle = RuntimePluginLifecycle()
        actions = RuntimePluginActionRegistry()
        operations = RuntimePluginOperations(
            lifecycle=lifecycle,
            action_registry=actions,
        )
        return RuntimePluginManager(
            registry=self.registry,
            loader=RuntimePluginLoader(),
            controller=RuntimePluginController(
                operations
            ),
            discovery=RuntimePluginDiscovery(
                Path("backend/runtime/plugins")
            ),
            capability_registry=self.capability_registry,
        )
    @property
    def manager(
        self,
    ) -> RuntimePluginManager:
        return self._manager
    def register_builtins(
        self,
        *,
        code_intelligence_workspace,
        code_intelligence_resolver,
        code_modification_provider,
        code_analyzer,
    ) -> None:
        if self._builtin_registered:
            return
        for category, plugin in builtin_plugins(
            tool_runtime_provider=self.tool_runtime_provider,
            workspace_root=self.workspace_root,
            code_intelligence_workspace=self.code_intelligence_workspace,
            code_intelligence_resolver=self.code_intelligence_resolver,
            code_modification_provider=code_modification_provider,
            code_analyzer=code_analyzer,
        ):
            self._register_plugin(
                category,
                plugin,
            )
        self._builtin_registered = True
    def _register_plugin(
        self,
        category: str,
        plugin: object,
    ) -> None:
        plugin.register(
            self.capability_registry
        )
        self.registry.register(
            category=category,
            name=plugin.name,
            component=plugin,
            version=plugin.version,
        )
    def resolve_plugin(
        self,
        category: str,
        name: str,
    ) -> object:
        return self.registry.resolve(
            category,
            name,
        )
    def register_capability(
        self,
        capability: RuntimeCapability,
        provider: object,
    ) -> None:
        self.capability_registry.register(
            capability,
            provider,
        )
    def resolve_capability(
        self,
        capability: RuntimeCapability | str,
        version: str | None = None,
    ) -> object:
        return self.capability_registry.resolve(
            capability,
            version,
        )
    def create_component(
        self,
        capability: str,
    ) -> object:
        return self.factory.create(
            capability
        )
    def has_component(
        self,
        capability: str,
    ) -> bool:
        return self.factory.has(
            capability
        )
    def discover_plugins(
        self,
    ) -> list:
        return self.manager.discover()
    def load_plugins(
        self,
    ) -> list:
        return self.manager.load_all()
    def ready(
        self,
    ) -> bool:
        return all(
            (
                self.manager.ready(),
                self.factory.ready(),
                self.capability_registry.ready(),
                self.tool_runtime_provider.ready(),
            )
        )
    def dump(
        self,
    ) -> dict[str, object]:
        return build_plugin_provider_snapshot(
            self
        )
__all__ = [
    "RuntimePluginProvider",
]
