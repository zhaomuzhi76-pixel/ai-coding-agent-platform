"""L1 契约层单测：ModelProvider 枚举、Intent 名称、WS payload 字段。"""
from __future__ import annotations

import re
from pathlib import Path

from .framework import Suite, assert_eq, assert_true


suite = Suite("contracts")


ROOT = Path(__file__).resolve().parents[3]
FE = ROOT / "frontend" / "src"


@suite.case
def model_contract_has_four_providers():
    """前端 ModelProvider 必须覆盖后端配置的 4 种 provider 类型。"""
    p = FE / "core" / "contracts" / "model.ts"
    text = p.read_text(encoding="utf-8")
    for prov in ("ollama", "openai_compatible", "dashscope", "anthropic"):
        assert_true(
            f'"{prov}"' in text,
            f"ModelProvider 缺少 {prov!r}",
        )
    return "4 providers present"


@suite.case
def model_contract_only_ollama_allows_empty_base_url():
    p = FE / "core" / "contracts" / "model.ts"
    text = p.read_text(encoding="utf-8")
    assert_true(
        'value.provider !== "ollama"' in text,
        "base_url 校验必须排除 ollama",
    )


@suite.case
def intent_contract_names_match_backend():
    """前端 Intent 契约名必须与后端 agent_entry/intent_router 严格一致。"""
    ts = (FE / "core" / "contracts" / "intent.ts").read_text(encoding="utf-8")
    py = (ROOT / "backend" / "application" / "agent_entry" / "intent_router.py").read_text(encoding="utf-8")

    ts_values = set(re.findall(r'"(\w+)"', ts))
    for name in ("query", "analyze", "modify", "create"):
        assert_true(name in ts_values, f"TS 缺 Intent {name!r}")
        assert_true(
            f'= "{name}"' in py,
            f"后端缺 Intent {name!r}",
        )
    return "4 intents aligned"


@suite.case
def ws_payload_fields_aligned():
    """前端 AgentSocketExecutionPayload 与后端 ws 收到的字段一致。"""
    ts = (FE / "core" / "websocket" / "agent_socket_protocol.ts").read_text(encoding="utf-8")
    # 前端 payload 字段
    m = re.search(
        r"interface AgentSocketExecutionPayload\s*\{([^}]+)\}",
        ts,
    )
    assert_true(m is not None, "找不到 AgentSocketExecutionPayload")
    fields = set(re.findall(r"^\s*(\w+):", m.group(1), re.M))
    for f in ("session_id", "message", "provider", "model", "workspace", "base_url", "api_key"):
        assert_true(f in fields, f"前端 payload 缺字段 {f!r}")
    return f"{len(fields)} fields"


@suite.case
def agent_loop_exposes_on_step():
    """agent_loop 必须暴露 on_step 回调（前端能接收每步）。"""
    base = ROOT / "backend" / "application" / "agent_loop"
    py = base / "agent_loop.py"
    found = "on_step" in py.read_text(encoding="utf-8")
    # 拆分后：检查 _agent_loop_parts/ 所有分片
    if not found:
        parts = base / "_agent_loop_parts"
        if parts.is_dir():
            for f in parts.rglob("*.py"):
                if "on_step" in f.read_text(encoding="utf-8"):
                    found = True
                    break
    assert_true(found, "agent_loop 缺 on_step 参数")
    return "on_step present"


@suite.case
def runtime_step_message_exists():
    """前端已定义 RuntimeStepMessage（可用于流式推步）。"""
    ts = (FE / "core" / "contracts" / "execution_event.ts").read_text(encoding="utf-8")
    assert_true(
        "RuntimeStepMessage" in ts,
        "execution_event.ts 缺 RuntimeStepMessage",
    )
    assert_true(
        '"step"' in ts,
        "RuntimeStepMessage.type 必须为 'step'",
    )
