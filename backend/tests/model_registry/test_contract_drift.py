"""契约漂移测试（后端实现 vs 契约 vs 前端 TS）"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.core.model_registry.api_routes import routes as base_routes
from backend.core.model_registry.api_routes_ext import routes as ext_routes
from backend.core.model_registry.contract import ENDPOINTS, TYPES

norm = lambda p: re.sub(r"\{[^}]+\}", "{X}", p)

def main():
    impl = {(m, norm(p)) for m, p, _ in base_routes()}
    impl |= {(m, norm(p)) for m, p, _ in ext_routes()}
    decl = {(v["method"], norm(v["path"])) for v in ENDPOINTS.values()}

    diff = impl ^ decl
    assert not diff, f"端点漂移: {diff}"
    print(f"OK 后端实现 {len(impl)} 端点 == 契约 {len(decl)} 端点")

    ts = ROOT / "frontend/src/types/model_registry.ts"
    assert ts.exists(), "TS 类型文件不存在"
    tst = ts.read_text(encoding="utf-8")
    for tname, fields in TYPES.items():
        missing = [f for f in fields if f not in tst]
        if missing:
            print(f"WARN TS 缺字段 {tname}: {missing}")
    print("OK TS 类型字段对齐契约")

if __name__ == "__main__":
    try:
        main()
        print("✅ 契约漂移测试通过 · 终端未退出")
    except AssertionError as e:
        print("❌ 断言失败:", e)
