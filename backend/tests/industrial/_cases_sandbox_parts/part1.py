"""Part 1 of cases_sandbox.py."""
from __future__ import annotations

import asyncio

import os

import tempfile

from backend.application.agent_loop.sandbox import (
    CommandNotAllowed,
    SandboxLimits,
    SandboxPolicyError,
    check_command,
    run_sandboxed,
)

from ..framework import Suite, assert_eq, assert_true

suite = Suite("sandbox")

@suite.case
def policy_rejects_sudo():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            check_command("sudo ls", tmp)
        except (SandboxPolicyError, CommandNotAllowed):
            return "ok"
    raise AssertionError("should reject sudo")

@suite.case
def policy_rejects_curl():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            check_command("curl http://x", tmp)
        except (SandboxPolicyError, CommandNotAllowed):
            return "ok"
    raise AssertionError("should reject curl")

@suite.case
def policy_allows_ls():
    with tempfile.TemporaryDirectory() as tmp:
        check_command("ls", tmp)
        return "ok"

@suite.case
def policy_blocks_git_push():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            check_command("git push origin main", tmp)
        except (SandboxPolicyError, CommandNotAllowed):
            return "ok"
    raise AssertionError("should reject git push")

@suite.case
def sandbox_ls_ok():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "a.py"), "w").close()
            return await run_sandboxed("ls", tmp)
    r = asyncio.run(主())
    assert_true(r["ok"])
    assert_true("a.py" in r["stdout"])
    return "ok"

@suite.case
def sandbox_python_print():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed(
                'python3 -c "print(2+2)"', tmp,
            )
    r = asyncio.run(主())
    assert_true(r["ok"])
    assert_true("4" in r["stdout"])
    return "ok"

@suite.case
def sandbox_truncates_output():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "big.txt"), "w").write("x" * 30000)
            return await run_sandboxed("cat big.txt", tmp)
    r = asyncio.run(主())
    assert_true(r.get("truncated") is True)
    assert_true(len(r["stdout"]) <= 10_100)
    return "ok"

@suite.case
def sandbox_timeout_kills():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed(
                'python3 -c "import time; time.sleep(60)"',
                tmp, timeout_sec=0.5,
            )
    r = asyncio.run(主())
    assert_true(r.get("timed_out") is True)
    assert_true(r.get("killed") is True)
    assert_true(not r["ok"])
    return "ok"

@suite.case
def sandbox_policy_error_returns():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("curl x", tmp)
    r = asyncio.run(主())
    assert_true(not r["ok"])
    assert_true("policy" in r.get("error", "").lower())
    return "ok"

@suite.case
def sandbox_python_c_forbidden():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed(
                'python3 -c "import os; os.system(\'ls\')"', tmp,
            )
    r = asyncio.run(主())
    assert_true(not r["ok"])
    return "ok"

@suite.case
def sandbox_custom_limits():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed(
                "ls", tmp,
                limits=SandboxLimits(cpu_seconds=10, memory_mb=128),
            )
    r = asyncio.run(主())
    assert_true(r["ok"])
    return "ok"

@suite.case
def sandbox_exit_code_propagates():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed('python3 -c "exit(3)"', tmp)
    r = asyncio.run(主())
    assert_eq(r["exit_code"], 3)
    assert_true(not r["ok"])
    return "ok"

@suite.case
def sandbox_namespace_active():
    """unshare 隔离是否生效（环境不支持时退化为 none，标记 skip）。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("ls", tmp)
    r = asyncio.run(主())
    ns = r.get("namespace", "")
    assert_true(ns in ("unshare", "none"), f"unexpected: {ns}")
    if ns == "none":
        return "skip (env not supported)"
    return f"namespace={ns}"

@suite.case
def sandbox_pid_namespace_isolated():
    """PID 命名空间内进程应看到小号 PID（< 10）。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("cat /proc/self/stat", tmp)
    r = asyncio.run(主())
    if r.get("namespace") != "unshare":
        return "skip"
    assert_true(r["ok"])
    pid_in_ns = int(r["stdout"].split()[0])
    assert_true(pid_in_ns <= 10, f"pid={pid_in_ns} 未隔离")
    return f"pid={pid_in_ns}"
