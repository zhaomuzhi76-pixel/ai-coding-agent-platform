"""intent_router + query_handler + dispatch 单测。"""
from __future__ import annotations

import asyncio
import os
import tempfile

from backend.application.agent_entry.intent_router import (
    Intent, route,
)
from backend.application.agent_entry.query_handler import handle_query
from backend.application.agent_entry import dispatch

from .framework import Suite, assert_eq, assert_in, assert_true


suite = Suite("agent_entry")


@suite.case
def route_query_zh():
    assert_eq(route("当前项目有多少个 py 文件"), Intent.QUERY)


@suite.case
def route_query_en():
    assert_eq(route("how many py files"), Intent.QUERY)


@suite.case
def route_analyze():
    assert_eq(route("分析这个项目在做什么"), Intent.ANALYZE)


@suite.case
def route_create():
    assert_eq(route("新建一个项目"), Intent.CREATE)


@suite.case
def route_modify():
    assert_eq(route("修复 main.py 的 bug"), Intent.MODIFY)


@suite.case
def route_readonly_marker():
    assert_eq(route("看看代码，不要修改"), Intent.QUERY)


@suite.case
def route_empty_defaults_modify():
    assert_eq(route(""), Intent.MODIFY)
    assert_eq(route("   "), Intent.MODIFY)


@suite.case
def query_count_py():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(7):
            open(os.path.join(tmp, f"f{i}.py"), "w").close()
        open(os.path.join(tmp, "readme.md"), "w").close()
        r = asyncio.run(handle_query("有多少个 py 文件", tmp))
        assert_true(r.get("success"), f"result={r}")
        assert_eq(r.get("count"), 7)
        return r.get("text", "")[:80]


@suite.case
def query_summary_no_ext():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(3):
            open(os.path.join(tmp, f"f{i}.py"), "w").close()
        for i in range(2):
            open(os.path.join(tmp, f"g{i}.ts"), "w").close()
        r = asyncio.run(handle_query("统计一下文件", tmp))
        assert_true(r.get("success"))
        assert_eq(r.get("total_files"), 5)


@suite.case
def query_invalid_workspace():
    r = asyncio.run(handle_query("查文件", "/nonexistent/xxx"))
    assert_true(not r.get("success"))
    assert_in("workspace not found", r.get("error", ""))


@suite.case
def query_skips_dot_git():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".git"))
        open(os.path.join(tmp, ".git", "config"), "w").close()
        open(os.path.join(tmp, "a.py"), "w").close()
        r = asyncio.run(handle_query("多少文件", tmp))
        assert_eq(r.get("total_files"), 1)


@suite.case
def dispatch_query_branch():
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "a.py"), "w").close()
        result = asyncio.run(
            dispatch({"message": "有几个 py", "workspace": tmp}, None)
        )
        assert_true(result is not None, "should return dict")
        assert_true(result.get("success"))


@suite.case
def dispatch_modify_without_gateway_returns_error():
    """契约：无 gateway 时 modify 返回结构化错误，不静默走 pipeline。"""
    result = asyncio.run(
        dispatch(
            {"message": "修复 a.py 的 bug", "workspace": "/tmp"},
            None,
        )
    )
    assert_true(result is not None, "must return dict")
    assert_true(result.get("success") is False, f"expected error, got {result}")
    assert_true(
        "gateway" in result.get("error", "").lower(),
        f"error should mention gateway: {result.get('error')}",
    )


@suite.case
def dispatch_unc_polluted_workspace():
    """端到端：模拟后端 CWD 污染的 workspace 字符串。"""
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(5):
            open(os.path.join(tmp, f"x{i}.py"), "w").close()
        polluted = (
            "/home/computer01/xiangmu02/biancheng_aiagentpro/"
            "\\\\wsl.localhost\\Ubuntu-24.04" + tmp
        )
        result = asyncio.run(
            dispatch(
                {"message": "几个 py", "workspace": polluted},
                None,
            )
        )
        assert_true(result is not None, "must return dict")
        # 工业级：必须真正成功，不允许"不抛异常"混过
        assert_true(
            result.get("success"),
            f"end-to-end must succeed, got {result}",
        )
        return f"success=True count={result.get('count')}"
