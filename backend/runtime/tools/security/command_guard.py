from __future__ import annotations

import shlex
from pathlib import Path


class ToolCommandGuard:
    """
    Workspace-bound terminal admission guard.

    Owns:
        - command shape validation
        - workspace path validation
        - destructive command rejection

    Does not own:
        - process execution
        - policy evaluation
        - approval lifecycle
    """

    VERSION = "1.0"

    BLOCKED = frozenset(
        {
            "shutdown",
            "reboot",
            "poweroff",
            "mkfs",
            "fdisk",
            "mount",
            "umount",
            "sudo",
            "su",
        }
    )

    # 写/改标志（重定向、管道、命令替换）
    WRITE_MARKERS = (">", ">>", "2>", "&>", "|", "$(", "`")

    def validate(self, command: str, workspace: str) -> None:
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command required")
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("workspace required")

        root = Path(workspace).expanduser().resolve(strict=False)
        if not root.exists() or not root.is_dir():
            raise ValueError("workspace directory required")

        try:
            tokens = shlex.split(command)
        except ValueError as error:
            raise ValueError(f"invalid command syntax: {error}") from error

        if not tokens:
            raise ValueError("command required")

        executable = Path(tokens[0]).name.lower()
        if executable in self.BLOCKED:
            raise PermissionError(
                f"blocked terminal command: {executable}"
            )

    def is_readonly(self, command: str, workspace: str = "/tmp") -> bool:
        """判断命令是否只读（可用于免审批执行）。

        数据源统一在 sandbox/policy.py（不重复白名单）：
          - 先过 policy.check_command（可执行性 + 危险命令 + 子命令白名单）
          - 命令中不得含写标志（> | $() 等）
          - 执行型可执行文件（python/npm/pytest...）可能写文件 → 一律走审批
        """
        if not isinstance(command, str) or not command.strip():
            return False
        for m in self.WRITE_MARKERS:
            if m in command:
                return False
        try:
            from backend.application.agent_loop.sandbox.policy import (
                check_command,
            )
            check_command(command, workspace)
        except Exception:
            return False
        try:
            tokens = shlex.split(command)
        except ValueError:
            return False
        if not tokens:
            return False
        exe = Path(tokens[0]).name.lower()
        # 执行型 + 可原地写文件型 → 一律走审批
        if exe in (
            "python", "python3", "python3.11",
            "npm", "yarn", "pnpm", "node",
            "pytest", "py.test",
            "sed", "awk", "perl", "ruby",
        ):
            return False
        return True

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "blocked_count": len(self.BLOCKED),
            "ready": self.ready(),
        }


__all__ = ["ToolCommandGuard"]
