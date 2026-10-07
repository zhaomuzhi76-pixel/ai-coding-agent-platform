"""L3 应用编排层单测：PlatformBackedCoordinator + dispatch 分流。"""
from __future__ import annotations

import asyncio
import os
import tempfile

from backend.application.agent_entry.agent_entry import (
    _resolve_provider_name,
    dispatch,
)

from .framework import Suite, assert_eq, assert_true


suite = Suite("coordinator")


@suite.case
def coordinator_class_exposes_execute():
    """PlatformBackedCoordinator 必须暴露 execute 方法（L3 唯一入口）。"""
    from backend.api.ws_platform_coordinator import (
        PlatformBackedCoordinator,
    )
    c = PlatformBackedCoordinator()
    assert_true(callable(getattr(c, "execute", None)), "execute 缺失")
    assert_true(callable(getattr(c, "ready", None)), "ready 缺失")
    return f"version={c.VERSION}"


@suite.case
def coordinator_has_gateway_fallback_logic():
    """execute 必须从 binding 提取 gateway（属性名 _gateway 或 gateway）。"""
    import inspect
    from backend.api.ws_platform_coordinator import (
        PlatformBackedCoordinator,
    )
    src = inspect.getsource(PlatformBackedCoordinator.execute)
    assert_true("_gateway" in src, "缺 _gateway 提取")
    assert_true("dispatch(" in src, "缺 dispatch 调用")


@suite.case
def dispatch_query_bypasses_gateway():
    """query 意图不依赖 gateway（只读快通道）。"""
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "x.py"), "w").close()
        result = asyncio.run(dispatch(
            {"message": "有多少 py 文件", "workspace": tmp},
            None,
            gateway=None,
        ))
        assert_true(result is not None, "query 不能返回 None")
        assert_true(result.get("success"), f"got {result}")


@suite.case
def dispatch_analyze_without_gateway_errors():
    """analyze 意图无 gateway 时返回结构化错误。"""
    result = asyncio.run(dispatch(
        {"message": "分析这个项目", "workspace": "/tmp"},
        None,
        gateway=None,
    ))
    assert_true(result is not None)
    assert_true(result.get("success") is False)
    assert_true("gateway" in result.get("error", "").lower())


@suite.case
def dispatch_normalizes_workspace_before_routing():
    """dispatch 应归一化 workspace（UNC 污染不会传到下游）。"""
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(3):
            open(os.path.join(tmp, f"m{i}.py"), "w").close()
        polluted = (
            "/home/x/y/"
            "\\\\wsl.localhost\\Ubuntu-24.04" + tmp
        )
        result = asyncio.run(dispatch(
            {"message": "几个 py 文件", "workspace": polluted},
            None,
        ))
        assert_true(result.get("success"), f"got {result}")
        assert_eq(result.get("count"), 3)


@suite.case
def resolve_provider_prefers_model_match():
    """provider 解析：model 名反查优先。

    工业级契约：不写死 provider 名，只验证：
      - 返回的 provider 确实存在于配置里
      - 该 provider 的 models 里包含目标 model
    """
    from backend.providers.config import load_llm_config
    cfg = load_llm_config()
    by_name = {p.name: p for p in cfg.providers}

    r = _resolve_provider_name("ollama", "qwen2.5-coder:7b")
    assert_eq(r, "ollama-local")

    # 通用契约：反查结果必须真的包含该 model
    target_model = "qwen3.8-max"
    r = _resolve_provider_name("openai_compatible", target_model)
    assert_true(
        r in by_name,
        f"resolved provider {r!r} not in configured: {list(by_name)}",
    )
    model_ids = [m.id for m in by_name[r].models]
    assert_true(
        target_model in model_ids,
        f"{r!r} does not contain model {target_model!r}: {model_ids}",
    )


@suite.case
def resolve_provider_direct_hit():
    """provider 名直接命中。"""
    r = _resolve_provider_name("ollama-local", "any")
    assert_eq(r, "ollama-local")


@suite.case
def resolve_provider_unknown_passthrough():
    """未知 provider 原样返回（不抛）。"""
    r = _resolve_provider_name("not-a-provider", "not-a-model")
    assert_eq(r, "not-a-provider")
