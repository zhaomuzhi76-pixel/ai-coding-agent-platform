"""一次性无痕测试 —— 全程 /dev/shm，不落盘，不退出终端。"""
from __future__ import annotations

import gc
import json
import shutil
import tempfile
from pathlib import Path


def _write_fixture(root: Path) -> None:
    (root / "good.py").write_text(
        '"""ok."""\n\n\ndef foo():\n    return 1\n',
        encoding="utf-8",
    )
    (root / "too_long.py").write_text(
        "\n".join(f"x = {i}" for i in range(260)),
        encoding="utf-8",
    )
    (root / "bad_exit.py").write_text(
        "import sys\n\nsys.exit(1)\n",
        encoding="utf-8",
    )


def run_test() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="std-", dir="/dev/shm"))
    results: dict[str, dict] = {}
    try:
        _write_fixture(tmp)

        # 1. 行数规则
        from backend.quality.standards.checks_basic import (
            check_line_limit, check_no_exit,
        )
        r_good = check_line_limit(tmp / "good.py", "good.py")
        r_long = check_line_limit(tmp / "too_long.py", "too_long.py")
        results["line_limit"] = {
            "ok": r_good.ok and not r_long.ok,
            "good": r_good.ok, "long_detected": not r_long.ok,
        }

        # 2. no_exit 规则
        r_exit = check_no_exit(tmp / "bad_exit.py", "bad_exit.py")
        results["no_exit"] = {"ok": not r_exit.ok}

        # 3. 契约
        from backend.quality.standards.contracts import (
            RULE_IDS, CheckResult, LayerReport,
        )
        rep = LayerReport(layer="x")
        rep.add(CheckResult("line_limit", True))
        rep.add(CheckResult("no_exit", False, "a.py", "bad"))
        results["contracts"] = {
            "ok": len(RULE_IDS) == 11 and not rep.ok
                  and len(rep.errors) == 1,
        }

        # 4. 重复职责检测器（不崩即过）
        from backend.quality.standards.checks_arch import (
            check_no_duplicate,
        )
        dup = check_no_duplicate(tmp, [tmp / "good.py"])
        results["no_duplicate_runs"] = {"ok": isinstance(dup, list)}

        # 5. CLI 可 import
        from backend.quality.standards import audit_cli, fix_cli
        results["cli_imports"] = {
            "ok": callable(audit_cli.run_audit)
                  and callable(fix_cli.run_fix),
        }

        overall = all(v.get("ok", False) for v in results.values())
        print(json.dumps(
            {"ok": overall, "tmpfs": str(tmp), "checks": results},
            ensure_ascii=False, indent=2,
        ))
        return 0 if overall else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        gc.collect()


__all__ = ["run_test"]


if __name__ == "__main__":
    import sys
    raise SystemExit(run_test())
