"""沙箱策略：危险命令 + 白名单。"""
from __future__ import annotations

import os
import shlex

from backend.runtime.tools.security.command_guard import (
    ToolCommandGuard,
)


class CommandNotAllowed(PermissionError):
    pass


class SandboxPolicyError(PermissionError):
    pass


_ALLOWED_EXECUTABLES = frozenset({
    "pytest", "py.test",
    "python", "python3", "python3.11",
    "npm", "yarn", "pnpm", "node",
    "git",
    "ls", "cat", "head", "tail", "wc", "grep",
    "find", "pwd", "echo", "which", "env",
    "uname", "whoami", "id", "date", "printenv",
    "file", "stat", "du", "df", "tree",
    # 注意：sed / awk 等可能 -i 原地写文件 → 不放白名单
})

_ALLOWED_GIT_SUBCMDS = frozenset({
    "status", "diff", "log", "show", "branch", "tag",
    "remote", "config", "ls-files", "rev-parse",
    "describe", "blame", "shortlog",
})

_ALLOWED_NPM_SUBCMDS = frozenset({
    "test", "run", "list", "ls", "why", "outdated", "audit",
})

_PYTHON_FORBIDDEN = (
    "os.system", "subprocess", "shutil.rmtree", "os.remove",
    "eval(", "exec(", "__import__",
)


def _check_whitelist(tokens: list[str]) -> None:
    if not tokens:
        raise CommandNotAllowed("empty command")
    exe = os.path.basename(tokens[0]).lower()
    if exe not in _ALLOWED_EXECUTABLES:
        raise CommandNotAllowed(f"executable not allowed: {exe!r}")
    if exe == "git" and len(tokens) >= 2:
        sub = tokens[1].lower()
        if not sub.startswith("-") and sub not in _ALLOWED_GIT_SUBCMDS:
            raise CommandNotAllowed(f"git subcommand not allowed: {sub!r}")
    if exe in ("npm", "yarn", "pnpm") and len(tokens) >= 2:
        sub = tokens[1].lower()
        if not sub.startswith("-") and sub not in _ALLOWED_NPM_SUBCMDS:
            raise CommandNotAllowed(
                f"{exe} subcommand not allowed: {sub!r}"
            )
    if exe in ("python", "python3", "python3.11"):
        for i, t in enumerate(tokens):
            if t == "-c" and i + 1 < len(tokens):
                code = tokens[i + 1]
                for f in _PYTHON_FORBIDDEN:
                    if f in code:
                        raise CommandNotAllowed(
                            f"python -c forbidden: {f!r}"
                        )


def check_command(command: str, workspace: str) -> None:
    if not command.strip():
        raise SandboxPolicyError("empty command")
    guard = ToolCommandGuard()
    try:
        guard.validate(command, workspace)
    except (PermissionError, ValueError) as exc:
        raise SandboxPolicyError(str(exc)) from exc

    # 写标志检测（重定向 / 管道 / 命令替换）—— 复用 guard.WRITE_MARKERS
    for marker in guard.WRITE_MARKERS:
        if marker in command:
            raise SandboxPolicyError(
                f"write marker not allowed in sandbox: {marker!r}"
            )

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise SandboxPolicyError(f"parse: {exc}") from exc
    try:
        _check_whitelist(tokens)
    except CommandNotAllowed as exc:
        raise SandboxPolicyError(str(exc)) from exc


__all__ = [
    "CommandNotAllowed", "SandboxPolicyError", "check_command",
]
