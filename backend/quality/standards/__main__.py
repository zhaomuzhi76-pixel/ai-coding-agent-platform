"""工业级规则集 CLI：audit / fix / test。

用法：
  python -m backend.quality.standards audit backend/agent/orchestration
  python -m backend.quality.standards fix   backend/agent/orchestration
  python -m backend.quality.standards test
"""
from __future__ import annotations

import argparse
import json
import sys


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="standards", add_help=True)
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("audit", help="一条命令审查整层")
    a.add_argument("layer", help="目标层目录，如 backend/agent/orchestration")
    a.add_argument("--json", action="store_true", help="JSON 输出")

    f = sub.add_parser("fix", help="一条命令修复整层")
    f.add_argument("layer", help="目标层目录")
    f.add_argument("--json", action="store_true")

    sub.add_parser("test", help="一次性无痕测试（不占硬盘）")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.cmd == "audit":
        from backend.quality.standards.audit_cli import run_audit
        r = run_audit(args.layer, as_json=args.json)
        return 0 if r == 0 else 1
    if args.cmd == "fix":
        from backend.quality.standards.fix_cli import run_fix
        r = run_fix(args.layer, as_json=args.json)
        return 0 if r == 0 else 1
    if args.cmd == "test":
        from backend.quality.standards.ephemeral_test import run_test
        r = run_test()
        return 0 if r == 0 else 1
    _parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
