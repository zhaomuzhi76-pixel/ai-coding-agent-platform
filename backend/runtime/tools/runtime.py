from __future__ import annotations

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.plugin_contract import ToolPluginProtocol
from backend.core.tools.result_contract import ToolResultProtocol
from backend.runtime.contracts.tool import (
    RuntimeToolContractProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.runtime.tools.alias import ToolAliasResolver
from backend.runtime.tools.argument_resolver import ToolArgumentResolver
from backend.runtime.tools.execution_gate import ToolExecutionGate
from backend.runtime.tools.registry import ToolRegistry
from backend.runtime.tools.security.command_guard import ToolCommandGuard


class ToolRuntime:
    """Workspace-scoped runtime boundary for tool execution."""

    NAME = "tools.runtime"
    VERSION = "12.0"
    name = NAME
    version = VERSION

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        alias_resolver: ToolAliasResolver | None = None,
        argument_resolver: ToolArgumentResolver | None = None,
        execution_gate: ToolExecutionGate | None = None,
        governance=None,
        workspace_root: str | None = None,
    ) -> None:
        if workspace_root is not None and not isinstance(workspace_root, str):
            raise TypeError("workspace_root must str")

        self.registry = registry or ToolRegistry()
        self.alias_resolver = alias_resolver or ToolAliasResolver()
        self.argument_resolver = argument_resolver or ToolArgumentResolver()
        self.workspace_root = workspace_root
        self.execution_gate = execution_gate or ToolExecutionGate(
            governance=governance,
            command_guard=ToolCommandGuard(),
            workspace_root=workspace_root,
        )
        self.execution_count = 0
        self.failure_count = 0

    def register_tool(
        self,
        tool: RuntimeToolContractProtocol,
    ) -> None:
        if tool is None:
            raise ValueError("tool required")
        name = tool.name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("tool name required")
        self.registry.register(name, tool)
        self.execution_gate.register_tool(name)

    def register_plugin(self, plugin: ToolPluginProtocol) -> None:
        if plugin is None:
            raise ValueError("plugin required")
        for tool in plugin.tools():
            self.register_tool(tool)

    def get_tool(self, name: str) -> RuntimeToolProtocol | None:
        return self.registry.get(self.resolve_tool_name(name))

    def resolve_tool_name(self, name: str) -> str:
        return self.alias_resolver.resolve(name)

    def resolve_arguments(
        self,
        name: str,
        arguments: ToolArguments,
    ) -> ToolArguments:
        return self.argument_resolver.resolve(name, arguments)

    async def execute(
        self,
        name: str,
        arguments: ToolArguments,
        *,
        role: str | None = None,
        request_id: str | None = None,
        action: str = "execute",
        resource: str | None = None,
        trace_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> ToolResultProtocol:
        try:
            resolved_name = self.resolve_tool_name(name)
            tool = self.registry.get(resolved_name)
            if tool is None:
                raise LookupError(f"tool unavailable: {resolved_name}")

            params = self.resolve_arguments(resolved_name, arguments)
            result = await self.execution_gate.execute(
                tool=tool,
                name=resolved_name,
                arguments=params,
                role=role,
                request_id=request_id,
                action=action,
                resource=resource,
                trace_id=trace_id,
                session_id=session_id,
                agent_id=agent_id,
            )
            self.execution_count += 1
            return result

        except Exception:
            self.failure_count += 1
            raise

    def ready(self) -> bool:
        return (
            self.registry.ready()
            and self.alias_resolver.ready()
            and self.argument_resolver.ready()
            and self.execution_gate.ready()
        )

    def snapshot(self) -> dict[str, int]:
        return {
            "execution_count": self.execution_count,
            "failure_count": self.failure_count,
            "audit_count": self.execution_gate.audit.count(),
        }

    def dump(self) -> ContextSnapshot:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": "runtime_tool_execution_boundary",
            "workspace_root": self.workspace_root,
            "ready": self.ready(),
            "registry": self.registry.dump(),
            "execution_gate": self.execution_gate.dump(),
        }


__all__ = ["ToolRuntime"]
