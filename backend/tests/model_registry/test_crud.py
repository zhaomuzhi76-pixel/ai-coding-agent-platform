"""CRUD 扩展测试（update / delete）"""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ["BIANCHENG_MODEL_STORE"] = str(Path(tempfile.gettempdir()) / "mr_crud.json")

from backend.core.model_registry import reset_registry, bootstrap_default, get_registry
from backend.core.model_registry.crud_ext import (
    delete_provider, list_all_models, update_provider, usage_kpi,
)

def main():
    reset_registry(); bootstrap_default()
    reg = get_registry()
    assert "ollama-local" in reg.providers
    n0 = len(reg.providers)

    r = update_provider("ollama-local", {"name": "本地 Ollama (改)"})
    assert r["ok"] and reg.providers["ollama-local"].name == "本地 Ollama (改)"
    print("OK update:", r)

    kpi = usage_kpi()
    assert kpi["total_models"] >= 2 and kpi["roles_routed"] == 5
    print("OK usage_kpi:", kpi)

    models = list_all_models()
    assert any(m["id"] == "qwen2.5-coder:7b" for m in models)
    print("OK list_all_models:", len(models))

    r = delete_provider("ollama-local")
    assert r["ok"] and "ollama-local" not in reg.providers
    assert len(reg.providers) == n0 - 1
    print("OK delete:", r, "剩余", len(reg.providers))

    try:
        delete_provider("not-exist")
        assert False
    except KeyError as e:
        print("OK delete 不存在:", e)

if __name__ == "__main__":
    try:
        main()
        print("✅ CRUD 测试通过 · 终端未退出")
    except AssertionError as e:
        print("❌ 断言失败:", e)
