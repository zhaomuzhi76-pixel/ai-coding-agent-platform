"""Part 2 of cases_approval.py."""
from __future__ import annotations
from .part1 import (assert_eq, assert_true, asyncio, maybe_intercept, suite, tempfile, write_actions,)  # noqa
from .part1 import _gate  # noqa

@suite.case
def interceptor_catches_write_actions():
    """写操作进入等待；由测试任务自行 approve。"""
    async def 主():
        with tempfile.TemporaryDirectory() as tmp:
            async def 批准():
                # 轮询 gate 拿 edit_id
                from backend.application.agent_loop.pending_gate import (
                    get_gate,
                )
                for _ in range(50):
                    await asyncio.sleep(0.02)
                    items = get_gate().list_pending()
                    if items:
                        await get_gate().approve(items[0]["edit_id"])
                        return
            task = asyncio.create_task(批准())
            result = await maybe_intercept(
                "file_write",
                {"path": "x.txt", "content": "hi"},
                tmp,
            )
            await task
            return result

    # maybe_intercept 用的是单例 gate（get_gate）
    from backend.application.agent_loop.pending_gate import get_gate
    # 先清空单例 pending（隔离历史）
    for item in get_gate().list_pending():
        get_gate().cleanup(item["edit_id"])

    assert_eq(asyncio.run(主()), "approved")

@suite.case
def write_actions_is_frozenset():
    actions = write_actions()
    # agent_loop 轻量集
    assert_true("write_file" in actions)
    assert_true("edit_file" in actions)
    assert_true("delete_file" in actions)
    # builtin 装配集
    assert_true("file_write" in actions)
    assert_true("file_edit" in actions)
    # 只读工具不应在白名单
    assert_true("read_file" not in actions)
    assert_true("file_read" not in actions)

@suite.case
def gate_dump_metadata():
    g = _gate()
    d = g.dump()
    assert_eq(d["name"], "PendingGate")
    assert_eq(d["pending"], 0)
