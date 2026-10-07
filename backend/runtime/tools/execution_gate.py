from __future__ import annotations

import asyncio
import time
from uuid import uuid4

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import ToolResultProtocol
from backend.runtime.contracts.tool import RuntimeToolContractProtocol
from backend.runtime.tools.audit import ToolAudit
from backend.runtime.tools.governance_executor import GovernanceExecutor
from backend.runtime.tools.permission import ToolPermission
from backend.runtime.tools.policy import ToolPolicy
from backend.runtime.tools.resource_limit import ResourceLimit
from backend.runtime.tools.security.command_guard import ToolCommandGuard
from backend.runtime.tools.validator import ToolValidator


class ToolExecutionGate:
    """Runtime tool execution admission coordinator."""

    VERSION = "3.1"
    DEFAULT_ROLE = "runtime"

    def __init__(
        self,
        *,
        validator: ToolValidator | None = None,
        governance: GovernanceExecutor | None = None,
        resource_limit: ResourceLimit | None = None,
        audit: ToolAudit | None = None,
        command_guard: ToolCommandGuard | None = None,
        workspace_root: str | None = None,
        default_role: str = DEFAULT_ROLE,
    ) -> None:
        if not isinstance(default_role, str) or not default_role.strip():
            raise ValueError("default role required")
        if workspace_root is not None and not workspace_root.strip():
            raise ValueError("workspace root cannot be empty")
        self.validator = validator or ToolValidator()
        self.resource_limit = resource_limit or ResourceLimit()
        self.audit = audit or ToolAudit()
        self.command_guard = command_guard or ToolCommandGuard()
        self.workspace_root = workspace_root
        self.default_role = default_role

        if governance is None:
            raise ValueError(
                "governance required"
            )

        self.governance = governance

    def register_tool(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("tool name required")
        self.governance.permission.grant(self.default_role, name)

    async def execute(
        self,
        *,
        tool: RuntimeToolContractProtocol,
        name: str,
        arguments: ToolArguments,
        role: str | None = None,
        request_id: str | None = None,
        action: str = "execute",
        resource: str | None = None,
        trace_id: str | None = None,
        session_id: str | None = None,
        agent_id: str | None = None,
    ) -> ToolResultProtocol:
        started = time.perf_counter()
        trace = trace_id or uuid4().hex
        selected_role = (role or self.default_role).strip()
        success = False
        error: str | None = None

        try:
            self._validate_tool(tool)
            params = self._validate_arguments(tool, arguments)
            self._check_governance(name, selected_role, request_id, action)
            self._check_command(name, params)
            self._check_input_limit(name, params)
            result = await self._invoke(tool, name, params)
            self._check_output_limit(name, result)
            success = True
            return result
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            self.audit.record(
                trace_id=trace,
                tool=name,
                success=success,
                duration=time.perf_counter() - started,
                error=error,
                session_id=session_id,
                agent_id=agent_id,
                action=action,
                resource=resource or name,
            )

    @staticmethod
    def _validate_tool(tool: RuntimeToolContractProtocol) -> None:
        if not isinstance(tool, RuntimeToolContractProtocol):
            raise TypeError(
                "tool must implement RuntimeToolContractProtocol"
            )

    def _validate_arguments(
        self,
        tool: RuntimeToolContractProtocol,
        arguments: ToolArguments,
    ) -> ToolArguments:
        result = self.validator.validate(tool.schema(), arguments)
        if not result["valid"]:
            raise ValueError("; ".join(str(item) for item in result["errors"]))
        return dict(result["arguments"])

    def _check_governance(
        self,
        name: str,
        role: str,
        request_id: str | None,
        action: str,
    ) -> None:
        decision = self.governance.evaluate(
            tool_name=name,
            role=role,
            request_id=request_id,
            action=action,
        )
        if not decision["allowed"]:
            raise PermissionError(f"tool execution denied: {name}")

    def _check_command(
        self,
        name: str,
        arguments: ToolArguments,
    ) -> None:
        if name != "terminal":
            return
        if not isinstance(self.workspace_root, str) or not self.workspace_root.strip():
            raise RuntimeError("terminal workspace root required")
        self.command_guard.validate(
            arguments.get("command"),
            self.workspace_root,
        )

    def _check_input_limit(
        self,
        name: str,
        arguments: ToolArguments,
    ) -> None:
        size = len(repr(arguments).encode("utf-8"))
        if not self.resource_limit.check_input_size(name, size):
            raise ValueError(f"tool input limit exceeded: {name}")

    def _check_output_limit(
        self,
        name: str,
        result: ToolResultProtocol,
    ) -> None:
        size = len(str(result.output).encode("utf-8"))
        if not self.resource_limit.check_output_size(name, size):
            raise ValueError(f"tool output limit exceeded: {name}")

    async def _invoke(
        self,
        tool: RuntimeToolContractProtocol,
        name: str,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        call = tool.execute(arguments)
        timeout = self.resource_limit.timeout(name)
        if timeout is None:
            return await call
        return await asyncio.wait_for(call, timeout=timeout)

    def ready(self) -> bool:
        return all(
            (
                self.validator.ready(),
                self.governance.ready(),
                self.resource_limit.ready(),
                self.audit.ready(),
                self.command_guard.ready(),
                self.workspace_root is None
                or bool(self.workspace_root.strip()),
                bool(self.default_role.strip()),
            )
        )

    def dump(self) -> ContextSnapshot:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "responsibility": "tool_execution_admission",
            "ready": self.ready(),
            "workspace_root": self.workspace_root,
            "command_guard": self.command_guard.dump(),
            "governance": self.governance.dump(),
        }


__all__ = ["ToolExecutionGate"]
