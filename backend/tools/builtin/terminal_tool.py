from __future__ import annotations

import asyncio

from backend.core.context.context_snapshot_contract import ContextSnapshot
from backend.core.tools.argument_contract import ToolArguments
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.tools.builtin.dependencies import (
    TerminalGuardProtocol,
)


class TerminalTool(RuntimeToolProtocol):
    name = "terminal"
    description = "Execute shell command in workspace"

    def __init__(
        self,
        workspace: str,
        guard: TerminalGuardProtocol,
    ) -> None:
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("workspace required")
        if not isinstance(guard, TerminalGuardProtocol):
            raise TypeError(
                "guard must TerminalGuardProtocol"
            )
        self.workspace = workspace
        self.guard = guard

    async def execute(
        self,
        arguments: ToolArguments,
    ) -> ToolResultProtocol:
        command = arguments.get("command")

        if not isinstance(command, str) or not command.strip():
            raise ValueError("command missing")

        self.guard.validate(
            command,
            self.workspace,
        )

        process = await asyncio.create_subprocess_shell(
            command,
            cwd=self.workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        return ToolResult.success_result(
            self.name,
            {
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout.decode(
                    "utf-8",
                    errors="ignore",
                ),
                "stderr": stderr.decode(
                    "utf-8",
                    errors="ignore",
                ),
            },
        )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=(
                ToolParameter(
                    name="command",
                    parameter_type="string",
                    description="workspace shell command",
                ),
            ),
        )

    def ready(self) -> bool:
        return (
            bool(self.workspace.strip())
            and self.guard.ready()
        )

    def dump(self) -> ContextSnapshot:
        return {
            "name": self.name,
            "version": "1.1",
            "responsibility": (
                "terminal_execution",
            ),
            "ready": self.ready(),
        }


__all__ = [
    "TerminalTool",
]
