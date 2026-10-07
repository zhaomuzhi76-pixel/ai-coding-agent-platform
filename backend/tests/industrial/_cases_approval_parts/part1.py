"""Part 1 of cases_approval.py."""
from __future__ import annotations

import asyncio

import os

import tempfile

from backend.application.agent_loop.approval_interceptor import (
    maybe_intercept, write_actions,
)

from backend.application.agent_loop.diff_generator import make_diff

from backend.application.agent_loop.pending_edit import PendingEdit

from backend.application.agent_loop.pending_gate import PendingGate

from ..framework import Suite, assert_eq, assert_in, assert_true

suite = Suite("approval")

def _gate() -> PendingGate:
    """每次测试用新 gate（不污染单例）。"""
    return PendingGate()

@suite.case
def pending_edit_creates_unique_id():
    a = PendingEdit.create("write_file", "a.txt", None, "x", "diff")
    b = PendingEdit.create("write_file", "a.txt", None, "x", "diff")
    assert_true(a.edit_id != b.edit_id)
    assert_true(a.edit_id.startswith("pe-"))

@suite.case
def pending_edit_to_wire_shape():
    e = PendingEdit.create("edit_file", "p/x.py", "old", "new", "d")
    w = e.to_wire()
    for k in ("edit_id", "action", "path", "diff",
              "created_at", "has_old", "has_new"):
        assert_in(k, w)
    assert_eq(w["action"], "edit_file")
    assert_eq(w["has_old"], True)
    assert_eq(w["has_new"], True)

@suite.case
def diff_generator_produces_unified():
    d = make_diff("a.py", "line1\nline2\n", "line1\nline2\nline3\n")
    assert_true("--- a/a.py" in d)
    assert_true("+++ b/a.py" in d)
    assert_true("+line3" in d)

@suite.case
def diff_generator_no_change():
    d = make_diff("a.py", "same\n", "same\n")
    assert_eq(d, "(no change)")

@suite.case
def diff_generator_truncates_large():
    big_old = "\n".join(f"old{i}" for i in range(5000))
    big_new = "\n".join(f"new{i}" for i in range(5000))
    d = make_diff("big.py", big_old, big_new)
    assert_true(len(d) <= 31_000)
    assert_true("[diff truncated]" in d)

@suite.case
def gate_approve_flow():
    async def 主():
        gate = _gate()
        e = PendingEdit.create("write_file", "x.txt", None, "hi", "d")

        async def 批准():
            await asyncio.sleep(0.05)
            await gate.approve(e.edit_id)

        await gate.request(e)
        task = asyncio.create_task(批准())
        result = await gate.wait(e.edit_id, timeout=2.0)
        await task
        return result

    assert_eq(asyncio.run(主()), "approved")

@suite.case
def gate_reject_flow():
    async def 主():
        gate = _gate()
        e = PendingEdit.create("delete_file", "x.txt", "old", None, "d")

        async def 拒绝():
            await asyncio.sleep(0.05)
            await gate.reject(e.edit_id)

        await gate.request(e)
        task = asyncio.create_task(拒绝())
        result = await gate.wait(e.edit_id, timeout=2.0)
        await task
        return result

    assert_eq(asyncio.run(主()), "rejected")

@suite.case
def gate_timeout_flow():
    async def 主():
        gate = _gate()
        e = PendingEdit.create("write_file", "x.txt", None, "hi", "d")
        await gate.request(e)
        return await gate.wait(e.edit_id, timeout=0.15)

    assert_eq(asyncio.run(主()), "timeout")

@suite.case
def gate_unknown_id():
    async def 主():
        gate = _gate()
        return await gate.wait("does-not-exist", timeout=0.1)

    assert_eq(asyncio.run(主()), "unknown")

@suite.case
def gate_approve_nonexistent_returns_false():
    async def 主():
        gate = _gate()
        return await gate.approve("nope")

    assert_eq(asyncio.run(主()), False)

@suite.case
def gate_list_pending():
    async def 主():
        gate = _gate()
        e1 = PendingEdit.create("write_file", "a.txt", None, "1", "d")
        e2 = PendingEdit.create("edit_file", "b.txt", "x", "y", "d")
        await gate.request(e1)
        await gate.request(e2)
        return gate.list_pending()

    items = asyncio.run(主())
    assert_eq(len(items), 2)
    paths = sorted(x["path"] for x in items)
    assert_eq(paths, ["a.txt", "b.txt"])

@suite.case
def gate_cleanup_removes():
    async def 主():
        gate = _gate()
        e = PendingEdit.create("write_file", "x.txt", None, "hi", "d")
        await gate.request(e)
        gate.cleanup(e.edit_id)
        return gate.list_pending()

    assert_eq(asyncio.run(主()), [])

@suite.case
def interceptor_ignores_read_actions():
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            return await maybe_intercept(
                "read_file", {"path": "x.txt"}, tmp,
            )

    assert_eq(asyncio.run(主()), None)
