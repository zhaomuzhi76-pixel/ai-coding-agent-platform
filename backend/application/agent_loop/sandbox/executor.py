"""沙箱执行器：命名空间隔离 + rlimit + 超时 SIGKILL。

隔离层：
    1. unshare 命名空间（user + mount + pid + net）—— 每命令独立隔离
    2. rlimit（CPU/内存/文件大小/句柄）—— 双保险
    3. 超时 SIGKILL —— 硬上限

降级策略：
    环境不支持 unshare 组合（WSL1、老内核、受限容器）→ 退回 rlimit-only
    探测结果一次性缓存，不重复探测。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import asyncio
import os
import shlex
import shutil
import signal
from typing import Optional

from .limits import SandboxLimits
from .policy import SandboxPolicyError, check_command

_DEFAULT_TIMEOUT = 30.0
_MAX_OUTPUT_BYTES = 10_000

_UNSHARE_BIN = shutil.which("unshare")
_NS_SUPPORTED: Optional[bool] = None

# unshare 命名空间标志（参考阿里云 Agent Sandbox + gVisor 语义）
#   --user --map-root-user  无 root 环境启用户命名空间
#   --mount                 独立挂载点（写不影响宿主）
#   --pid --fork            独立进程树
#   --mount-proc            重新挂载 /proc（pid 隔离前提）
#   --net                   独立网络（仅 loopback）
_NS_FLAGS = (
    "--user", "--map-root-user",
    "--mount", "--pid", "--fork", "--mount-proc", "--net",
)


def _detect_namespace_support() -> bool:
    """探测 unshare 是否支持完整命名空间组合。结果缓存。"""
    global _NS_SUPPORTED
    if _NS_SUPPORTED is not None:
        return _NS_SUPPORTED
    if not _UNSHARE_BIN:
        _NS_SUPPORTED = False
        return False
    try:
        import subprocess
        r = subprocess.run(
            [_UNSHARE_BIN, *_NS_FLAGS, "true"],
            capture_output=True, timeout=2,
        )
        _NS_SUPPORTED = (r.returncode == 0)
    except Exception:
        _NS_SUPPORTED = False
    return _NS_SUPPORTED


def _wrap_with_rlimit(command: str, limits: SandboxLimits) -> str:
    """用 ulimit 包装命令（在命名空间内生效）。"""
    kb_mem = limits.memory_mb * 1024
    blocks_fs = limits.file_size_mb * 2048  # 512B/block
    return (
        f"ulimit -t {limits.cpu_seconds} 2>/dev/null; "
        f"ulimit -v {kb_mem} 2>/dev/null; "
        f"ulimit -f {blocks_fs} 2>/dev/null; "
        f"ulimit -n {limits.open_files} 2>/dev/null; "
        f"{command}"
    )


async def _spawn(command: str, workspace: str, use_ns: bool):
    """优先 argv-exec（namespace）；降级 shell（rlimit-only）。"""
    inner = command
    if use_ns:
        argv = [_UNSHARE_BIN, *_NS_FLAGS, "/bin/sh", "-c", inner]
        return await asyncio.create_subprocess_exec(
            *argv,
            cwd=workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
    return await asyncio.create_subprocess_shell(
        inner,
        cwd=workspace,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )


async def run_sandboxed(
    command: str,
    workspace: str,
    *,
    timeout_sec: float = _DEFAULT_TIMEOUT,
    limits: Optional[SandboxLimits] = None,
) -> dict:
    try:
        check_command(command, workspace)
    except SandboxPolicyError as exc:
        return {"ok": False, "error": f"policy: {exc}"}
    except Exception as exc:
        return {"ok": False, "error": f"policy: {exc}"}

    eff = limits or SandboxLimits()
    inner = _wrap_with_rlimit(command, eff)
    use_ns = _detect_namespace_support()

    try:
        proc = await _spawn(inner, workspace, use_ns)
    except Exception as exc:
        return {"ok": False, "error": f"spawn: {exc}"}

    timed_out = killed = False
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_sec,
        )
    except asyncio.TimeoutError:
        timed_out = killed = True
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception as e:
                swallow("application.agent_loop.sandbox.executor:133", e)
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except Exception as e:
            swallow("application.agent_loop.sandbox.executor:137", e)
        stdout_b, stderr_b = b"", b""

    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")
    truncated = False
    if len(stdout) > _MAX_OUTPUT_BYTES:
        stdout = stdout[:_MAX_OUTPUT_BYTES] + "\n...[truncated]"
        truncated = True
    if len(stderr) > _MAX_OUTPUT_BYTES:
        stderr = stderr[:_MAX_OUTPUT_BYTES] + "\n...[truncated]"
        truncated = True

    exit_code = proc.returncode if proc.returncode is not None else -1
    return {
        "ok": exit_code == 0 and not timed_out,
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": truncated,
        "timed_out": timed_out,
        "killed": killed,
        "namespace": "unshare" if use_ns else "none",
    }


__all__ = ["run_sandboxed"]
