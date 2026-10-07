"""L2 agent_loop 领域层单测。"""
from __future__ import annotations

import asyncio
import os
import tempfile

from backend.application.agent_loop import run_agent_loop
from backend.application.agent_loop.tool_registry import specs, dispatch_tool
from backend.application.agent_loop.prompt_builder import parse_action
from backend.application.agent_loop.observation import render

from .framework import Suite, assert_eq, assert_in, assert_true


suite = Suite("agent_loop")


class FakeGateway:
    def __init__(self, script):
        self.script = list(script)
        self.i = 0

    async def chat(self, provider, messages, model, **kw):
        if self.i >= len(self.script):
            raise RuntimeError("script exhausted")
        r = self.script[self.i]
        self.i += 1
        return r


@suite.case
def specs_has_required_tools():
    names = {s.name for s in specs()}
    for want in ("read_file", "list_dir", "grep", "count_files"):
        assert_in(want, names, "missing tool")
    return f"{len(names)} tools"


@suite.case
def tool_count_files_ext():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(3):
            open(os.path.join(tmp, f"a{i}.py"), "w").close()
        open(os.path.join(tmp, "b.md"), "w").close()
        r = asyncio.run(dispatch_tool("count_files", {"ext": ".py"}, tmp))
        assert_true(r["ok"])
        assert_eq(r["matched"], 3)
        assert_eq(r["total"], 4)


@suite.case
def tool_read_file_traversal_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        r = asyncio.run(
            dispatch_tool("read_file", {"path": "../../etc/passwd"}, tmp)
        )
        assert_true(not r["ok"])


@suite.case
def tool_unknown_rejected():
    r = asyncio.run(dispatch_tool("not_a_tool", {}, "/tmp"))
    assert_true(not r["ok"])


@suite.case
def parse_action_handles_qwen_tool_call_tag():
    raw = '<tool_call>\n{"action":"read_file","args":{"path":"a.py"}}\n</tool_call>'
    obj = parse_action(raw)
    assert_eq(obj.get("action"), "read_file")


@suite.case
def parse_action_picks_last_json_in_multi():
    raw = '{"action":"a"} 说明 {"action":"b","done":true}'
    obj = parse_action(raw)
    assert_true(
        obj.get("action") == "b" or obj.get("done") is True,
        f"got {obj}",
    )


@suite.case
def observation_render_count():
    obs = render({"ok": True, "matched": 3, "total": 10, "ext": ".py"})
    assert_true("matched=3" in obs)


@suite.case
def observation_render_error():
    obs = render({"ok": False, "error": "boom"})
    assert_true("ERROR: boom" in obs)


@suite.case
def loop_completes_in_two_steps():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(3):
            open(os.path.join(tmp, f"m{i}.py"), "w").close()
        gw = FakeGateway([
            '{"action":"count_files","args":{"ext":".py"}}',
            '{"done":true,"answer":"3"}',
        ])
        res = asyncio.run(run_agent_loop(
            task="数", workspace=tmp, gateway=gw,
            provider="ollama-local", model="x", max_steps=5,
        ))
        assert_true(res["success"])
        assert_eq(res["steps"], 2)
        assert_eq(len(res["trace"]), 2)


@suite.case
def loop_respects_max_steps():
    gw = FakeGateway(['{"action":"count_files","args":{}}'] * 10)
    res = asyncio.run(run_agent_loop(
        task="x", workspace="/tmp", gateway=gw,
        provider="ollama-local", model="x", max_steps=3,
    ))
    assert_true(not res["success"])
    assert_in("max steps", res["error"])


@suite.case
def loop_rejects_empty_task():
    res = asyncio.run(run_agent_loop(
        task="", workspace="/tmp",
        gateway=FakeGateway([]), provider="x", model="x",
    ))
    assert_true(not res["success"])


@suite.case
def loop_rejects_missing_gateway():
    res = asyncio.run(run_agent_loop(
        task="x", workspace="/tmp", gateway=None,
        provider="x", model="x",
    ))
    assert_true(not res["success"])


@suite.case
def loop_invokes_on_step_callback():
    called = []
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "a.py"), "w").close()
        gw = FakeGateway([
            '{"action":"count_files","args":{"ext":".py"}}',
            '{"done":true,"answer":"1"}',
        ])
        res = asyncio.run(run_agent_loop(
            task="数", workspace=tmp, gateway=gw,
            provider="ollama-local", model="x", max_steps=3,
            on_step=lambda entry: called.append(entry),
        ))
        assert_true(res["success"])
        assert_eq(len(called), 1)
        assert_eq(called[0]["action"], "count_files")
