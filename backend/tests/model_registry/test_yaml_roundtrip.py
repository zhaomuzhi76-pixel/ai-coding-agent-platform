"""YAML/JSON 导入导出往返测试"""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ["BIANCHENG_MODEL_STORE"] = str(Path(tempfile.gettempdir()) / "mr_roundtrip.json")
os.environ["DASHSCOPE_API_KEY"] = "sk-roundtrip"

from backend.core.model_registry import reset_registry, bootstrap_default, get_registry
from backend.core.model_registry.config_io import export_json, export_yaml, import_json

def main():
    reset_registry(); bootstrap_default()
    reg = get_registry()
    p0, r0 = len(reg.providers), len(reg.roles)

    j = export_json(reg)
    y = export_yaml(reg)
    assert '"providers"' in j and "providers:" in y, "导出失败"
    print(f"OK export json={len(j)}b  yaml={len(y)}b")

    reset_registry()
    reg2 = get_registry()
    reg2.discover_models()
    n = import_json(reg2, j)
    assert n == p0, f"导入 provider 数量不符: {n} vs {p0}"
    assert len(reg2.roles) == r0, f"导入 roles 数量不符"
    print(f"OK roundtrip: providers={n} roles={len(reg2.roles)}")

if __name__ == "__main__":
    try:
        main()
        print("✅ YAML/JSON 往返测试通过 · 终端未退出")
    except AssertionError as e:
        print("❌ 断言失败:", e)
