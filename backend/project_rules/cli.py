"""命令行入口：python -m backend.project_rules.cli"""
from __future__ import annotations

import argparse
import sys

from .rule_runner import format_report, run_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="project_rules")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--report", default="-", help="报告输出（- 表示 stdout）")
    args = parser.parse_args(argv)

    report = run_all(args.root)
    lines = format_report(report)
    out = "\n".join(lines)
    if args.report == "-":
        print(out)
    else:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(out)
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
