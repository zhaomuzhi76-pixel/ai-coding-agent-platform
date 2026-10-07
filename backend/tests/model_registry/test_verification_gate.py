"""验证门禁测试：只有通过链路测试的模型才能进入 Agent 下拉"""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ["BIANCHENG_MODEL_STORE"] = str(Path(tempfile.gettempdir()) / "mr_verify.json")
os.environ["BIANCHENG_OFFLINE"] = "1"
os.environ["DASHSCOPE_API_KEY"] = "sk-gate"

from backend.core.model_registry import reset_registry, bootstrap_default, get_registry
from backend.core.model_registry.facade import get_facade


def main():
    reset_registry(); bootstrap_default()
    reg = get_registry()
    f = get_facade()

    assert reg.verification.list_verified() == []
    assert f.verified_models() == []
    print("OK 未测试 -> Agent 下拉为空")

    res = f.test_and_verify_provider("ollama-local")
    assert res["ok"] is True, res
    verified = reg.verification.list_verified()
    assert len(verified) >= 2
    print("OK 测试通过 -> verified:", verified)

    drop = f.verified_models()
    labels = [d["display_name"] for d in drop]
    assert all(" · " in x for x in labels)
    print("OK Agent 下拉:", labels)

    assert not any("qwen-max" == d["id"] for d in drop)
    print("OK 未测试的 dashscope 不在下拉里")

    res = f.test_and_verify_provider("dashscope-qwen")
    assert res["ok"] is True
    drop2 = f.verified_models()
    assert any(d["id"] == "qwen-max" for d in drop2)
    print("OK dashscope 测试后进入下拉:", [d["id"] for d in drop2])

    reg.verification.mark_failed("qwen-max", "test fail")
    drop3 = f.verified_models()
    assert not any(d["id"] == "qwen-max" for d in drop3)
    print("OK 失败撤销后从下拉移除")

    print("✅ 验证门禁测试通过 · 终端未退出")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("❌ 断言失败:", e); sys.exit(1)
