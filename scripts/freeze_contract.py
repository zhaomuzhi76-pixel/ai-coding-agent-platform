"""契约冻结：导出 model_registry 的版本化 JSON 契约"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.core.model_registry.contract import build_schema, CONTRACT_VERSION


def main(out_path: str) -> int:
    target = ROOT / out_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ 契约冻结 v{CONTRACT_VERSION} → {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "contracts/model_registry.v1.json"
    sys.exit(main(arg))
