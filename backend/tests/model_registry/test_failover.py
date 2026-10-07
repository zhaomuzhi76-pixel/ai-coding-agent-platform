"""fallback 降级真实容灾测试（mock 云端抛异常，验证切到本地）"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

os.environ["BIANCHENG_MODEL_STORE"] = str(
    Path(tempfile.gettempdir()) / "mr_failover.json"
)
os.environ["DASHSCOPE_API_KEY"] = "sk-failover-test"

from backend.core.model_registry import (
    bootstrap_default, get_registry, reset_registry,
)
from backend.core.model_registry.domain import RoleRoute


def _setup():
    reset_registry()
    bootstrap_default()
    reg = get_registry()
    reg.set_role_route(RoleRoute(
        role="code",
        primary="qwen-max",              # 云端
        fallback="qwen2.5-coder:7b",     # 本地兜底
    ))
    return reg


def test_normal_path_uses_primary():
    reg = _setup()
    out = reg.generate("code", "hi")
    assert "dashscope/qwen-max" in out, out
    print("✅ 正常路径走 primary:", out)


def test_primary_down_falls_back():
    reg = _setup()
    cloud_pid = reg.models["qwen-max"].provider_id
    with patch.object(
        reg.plugins[cloud_pid], "generate",
        side_effect=ConnectionError("cloud down"),
    ):
        out = reg.generate("code", "hi")
    assert "ollama/qwen2.5-coder:7b" in out, out
    print("✅ 云端断网自动降级到本地:", out)


def test_both_down_raises_with_details():
    reg = _setup()
    cloud_pid = reg.models["qwen-max"].provider_id
    local_pid = reg.models["qwen2.5-coder:7b"].provider_id
    with patch.object(reg.plugins[cloud_pid], "generate",
                      side_effect=ConnectionError("cloud down")):
        with patch.object(reg.plugins[local_pid], "generate",
                          side_effect=RuntimeError("local down")):
            try:
                reg.generate("code", "hi")
                assert False, "should raise"
            except RuntimeError as exc:
                msg = str(exc)
                assert "cloud down" in msg and "local down" in msg, msg
                print("✅ 双路失败抛聚合错误:", msg[:80] + "...")


def test_unrouted_role_raises():
    reg = _setup()
    try:
        reg.generate("nonexistent", "hi")
        assert False, "should raise"
    except KeyError as exc:
        print("✅ 未路由角色报 KeyError:", exc)


if __name__ == "__main__":
    test_normal_path_uses_primary()
    test_primary_down_falls_back()
    test_both_down_raises_with_details()
    test_unrouted_role_raises()
    print("✅ 容灾测试全部通过 · 终端未退出")
