"""run_command：委托给沙箱执行器。

契约：
    - 策略检查（危险命令 + 白名单）在 sandbox/policy
    - 执行在 sandbox/executor（子进程 + rlimit + 超时 SIGKILL）
    - 本文件只做工具声明 + dispatch 转发
"""
from __future__ import annotations

from .sandbox import run_sandboxed
from .tool_spec import ToolSpec

_TIMEOUT_SEC = 30.0

RUN_COMMAND_TOOL = ToolSpec(
    "run_command",
    "执行白名单内的 shell 命令（pytest / git status / ls 等）。",
    {"command": "要执行的命令"},
)


async def dispatch_run_command(
    name: str, args: dict, workspace: str,
) -> dict:
    if name != "run_command":
        return {"ok": False, "error": f"unknown: {name}"}
    command = str(args.get("command", ""))
    if not command.strip():
        return {"ok": False, "error": "command required"}
    return await run_sandboxed(
        command, workspace, timeout_sec=_TIMEOUT_SEC,
    )


__all__ = ["RUN_COMMAND_TOOL", "dispatch_run_command"]
