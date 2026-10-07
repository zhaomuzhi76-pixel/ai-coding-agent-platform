"""工业级一次性严格测试入口。

用法：
    python3 -m backend.tests.industrial.run
"""
from __future__ import annotations

from .framework import SuiteReport
from .cases_workspace import suite as ws_suite
from .cases_agent_entry import suite as ae_suite
from .cases_contracts import suite as ct_suite
from .cases_agent_loop import suite as al_suite
from .cases_coordinator import suite as co_suite
from .cases_l4_boundary import suite as l4_suite
from .cases_approval import suite as ap_suite
from .cases_sandbox import suite as sb_suite
from .cases_rag_governance import suite as rg_suite


def _fmt(rep: SuiteReport, name: str) -> list[str]:
    lines = ["", f"─── 套件: {name} ───"]
    for r in rep.results:
        icon = "PASS" if r.passed else "FAIL"
        line = f"  [{icon}] {r.name}  ({r.duration_ms:.1f}ms)"
        if r.detail and r.passed:
            line += f"  -> {r.detail}"
        lines.append(line)
        if not r.passed:
            lines.append(f"         {r.error}")
            for ln in r.detail.splitlines()[-5:]:
                lines.append(f"         {ln}")
    lines.append(f"  小计: {rep.passed}/{rep.total}")
    return lines


def main() -> int:
    print("=" * 51)
    print("  工业级一次性严格测试")
    print("=" * 51)

    total = passed = 0
    for name, suite in (
        ("workspace_layer", ws_suite),
        ("agent_entry", ae_suite),
        ("contracts", ct_suite),
        ("agent_loop", al_suite),
        ("coordinator", co_suite),
        ("l4_boundary", l4_suite),
        ("approval", ap_suite),
        ("sandbox", sb_suite),
        ("rag_governance", rg_suite),
    ):
        rep = suite.run()
        for ln in _fmt(rep, name):
            print(ln)
        total += rep.total
        passed += rep.passed

    print()
    print("=" * 51)
    print(f"  总计: {passed}/{total}")
    print(f"  结果: {'全部通过' if passed == total else f'{total - passed} 个失败'}")
    print("=" * 51)
    return 0 if passed == total else 1


if __name__ == "__main__":
    # 不用 sys.exit —— 脚本自然结束，终端不退出
    main()
