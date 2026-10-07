from __future__ import annotations

from backend.core.tools.execution_contract import (
    ToolCapabilityProtocol,
)
from backend.runtime.bootstrap.runtime_tool_execution_adapter import (
    RuntimeToolExecutionAdapter,
)
from backend.runtime.executors.tool_execution_port import (
    ToolExecutionPort,
)
from backend.runtime.plugins.executors.plugin import (
    RuntimeExecutorPlugin,
)
from backend.runtime.tools.runtime import (
    ToolRuntime,
)


class RuntimeExecutorPluginBinder:
    """
    Runtime executor plugin dependency binder.

    Responsibility:
        - locate executor plugin
        - bind runtime dependencies
        - install workspace-scoped tool execution
        - activate executor resolver capability

    Not Responsible:
        - plugin discovery
        - executor implementation
        - application workflow
        - DAG execution
    """

    VERSION = "2.0"

    def __init__(
        self,
        plugin_provider,
        *,
        tool_runtime_provider,
    ) -> None:
        if plugin_provider is None:
            raise ValueError(
                "plugin provider required"
            )

        if tool_runtime_provider is None:
            raise ValueError(
                "tool runtime provider required"
            )

        self.plugin_provider = plugin_provider
        self.tool_runtime_provider = (
            tool_runtime_provider
        )

    def bind(
        self,
        *,
        llm_provider,
        tools,
        modification,
    ) -> RuntimeExecutorPlugin:
        if llm_provider is None:
            raise ValueError(
                "llm provider required"
            )

        if tools is None:
            raise ValueError(
                "tool capability required"
            )

        if modification is None:
            raise ValueError(
                "modification provider required"
            )

        tool_port = self._create_tool_port(
            tools
        )

        plugin = self.plugin_provider.resolve_plugin(
            "executor",
            "executors",
        )

        if not isinstance(
            plugin,
            RuntimeExecutorPlugin,
        ):
            raise TypeError(
                "executor plugin must RuntimeExecutorPlugin"
            )

        plugin.configure(
            llm_provider=llm_provider,
            tools=tool_port,
            modification=modification,
        )

        plugin.activate(
            self.plugin_provider.capability_registry
        )

        if not plugin.ready():
            raise RuntimeError(
                "executor plugin not ready"
            )

        return plugin

    def ready(
        self,
    ) -> bool:
        try:
            plugin = self.plugin_provider.resolve_plugin(
                "executor",
                "executors",
            )
        except LookupError:
            return False

        return (
            isinstance(
                plugin,
                RuntimeExecutorPlugin,
            )
            and plugin.ready()
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    def _create_tool_port(
        self,
        tools: object,
    ) -> ToolExecutionPort:
        if isinstance(
            tools,
            ToolExecutionPort,
        ):
            if not tools.ready():
                raise RuntimeError(
                    "tool execution port not ready"
                )
            return tools

        capability = self._create_tool_capability(
            tools
        )

        port = ToolExecutionPort(
            capability=capability
        )

        if not port.ready():
            raise RuntimeError(
                "tool execution port unavailable"
            )

        return port

    def _create_tool_capability(
        self,
        tools: object,
    ) -> ToolCapabilityProtocol:
        if isinstance(
            tools,
            ToolRuntime,
        ):
            capability = RuntimeToolExecutionAdapter(
                self.tool_runtime_provider
            )

            if not capability.ready():
                raise RuntimeError(
                    "runtime tool adapter not ready"
                )

            return capability

        if not isinstance(
            tools,
            ToolCapabilityProtocol,
        ):
            raise TypeError(
                "tools must implement ToolCapabilityProtocol"
            )

        return tools


__all__ = [
    "RuntimeExecutorPluginBinder",
]
