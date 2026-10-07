"""Part 2 of cases_sandbox.py."""
from __future__ import annotations
from .part1 import (assert_eq, assert_true, asyncio, os, run_sandboxed, suite, tempfile,)  # noqa

@suite.case
def sandbox_net_namespace_isolated():
    """net 命名空间内应只有 lo 接口。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("cat /proc/net/dev", tmp)
    r = asyncio.run(主())
    if r.get("namespace") != "unshare":
        return "skip"
    assert_true(r["ok"])
    ifaces = [
        line.split(":")[0].strip()
        for line in r["stdout"].splitlines()
        if ":" in line and "face" not in line and "Inter-" not in line
    ]
    assert_eq(ifaces, ["lo"])
    return f"ifaces={ifaces}"

@suite.case
def sandbox_blocks_redirect():
    """重定向写文件应被拦（写标志检测）。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("echo evil > /tmp/sandbox_x", tmp)
    r = asyncio.run(主())
    assert_true(not r["ok"])
    assert_true("policy" in r.get("error", "").lower())
    return "ok"

@suite.case
def sandbox_blocks_pipe():
    """管道应被拦。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("cat a | tee b", tmp)
    r = asyncio.run(主())
    assert_true(not r["ok"])
    assert_true("policy" in r.get("error", "").lower())
    return "ok"

@suite.case
def sandbox_blocks_command_substitution():
    """命令替换（$(...) 和反引号）应被拦。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            r1 = await run_sandboxed("echo $(id)", tmp)
            r2 = await run_sandboxed("echo `id`", tmp)
            return r1, r2
    r1, r2 = asyncio.run(主())
    assert_true(not r1["ok"])
    assert_true(not r2["ok"])
    return "ok"

@suite.case
def sandbox_git_readonly_in_real_repo():
    """真 git repo 里只读子命令应放行。"""
    import subprocess
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "a.txt"), "w").write("x")
            subprocess.run(["git", "init", "-q"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "add", "a.txt"], cwd=tmp, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp, capture_output=True)
            return await run_sandboxed("git status", tmp)
    r = asyncio.run(主())
    assert_true(r["ok"], f"git status exit={r.get('exit_code')}")
    return "ok"

@suite.case
def sandbox_git_write_blocked():
    """git 写子命令应被拦。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await run_sandboxed("git push origin main", tmp)
    r = asyncio.run(主())
    assert_true(not r["ok"])
    assert_true("policy" in r.get("error", "").lower())
    return "ok"
