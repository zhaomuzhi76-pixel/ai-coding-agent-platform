"""迁移回归安全门：对每个 .py.bak 做语法级新旧双版本验证

不 import 被测文件（避免触发副作用），只做 AST 解析。
"""
import ast
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _parse(p: Path) -> Tuple[bool, str]:
    try:
        ast.parse(p.read_text(encoding="utf-8"))
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError L{e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def _collect_pairs() -> list:
    pairs = []
    for bak in sorted(BACKEND.rglob("*.py.bak")):
        if "model_registry" in bak.parts:
            continue
        new = bak.with_suffix("")
        if new.exists():
            pairs.append((new, bak))
    return pairs


def main() -> int:
    pairs = _collect_pairs()
    if not pairs:
        print("ℹ️  未发现迁移备份文件")
        return 0
    ok = fail = 0
    for new, old in pairs:
        n_ok, n_err = _parse(new)
        o_ok, o_err = _parse(old)
        rel = new.relative_to(ROOT)
        if n_ok and o_ok:
            ok += 1
            print(f"✅ {rel}")
        else:
            fail += 1
            if not n_ok:
                print(f"❌ {rel}  [新] {n_err}")
            if not o_ok:
                print(f"❌ {rel}  [旧] {o_err}")
    print(f"--- 通过 {ok} / 失败 {fail} / 总 {len(pairs)} ---")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
