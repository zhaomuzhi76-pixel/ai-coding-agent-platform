"""项目规则 CLI：导入 / 检测冲突 / 查看继承。

用法：
  python -m backend.agent_learning.rules_cli import <file> [--workspace W]
  python -m backend.agent_learning.rules_cli conflicts [--workspace W]
  python -m backend.agent_learning.rules_cli inherit <workspace>
"""
from __future__ import annotations

import argparse
import json
import sys


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rules", add_help=True)
    sub = p.add_subparsers(dest="cmd")

    i = sub.add_parser("import", help="导入 .rules 文件")
    i.add_argument("file")
    i.add_argument("--workspace", default="")
    i.add_argument("--scope", default="project")
    i.add_argument("--json", action="store_true")

    c = sub.add_parser("conflicts", help="检测冲突")
    c.add_argument("--workspace", default="")
    c.add_argument("--json", action="store_true")

    h = sub.add_parser("inherit", help="查看继承链")
    h.add_argument("workspace")
    h.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.cmd == "import":
        return _cmd_import(args)
    if args.cmd == "conflicts":
        return _cmd_conflicts(args)
    if args.cmd == "inherit":
        return _cmd_inherit(args)
    _parser().print_help()
    return 0


def _cmd_import(args) -> int:
    from backend.agent_learning.rules_importer import import_file
    r = import_file(args.file, workspace=args.workspace,
                    scope=args.scope)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"✅ 导入 {r.get('imported', 0)} 条规则")
        print(f"   file={r.get('source_path')}  ws={r.get('workspace')}")
        if r.get("errors"):
            for e in r["errors"]:
                print(f"   ⚠️ {e}")
    return 0 if r.get("ok") else 1


def _cmd_conflicts(args) -> int:
    from backend.agent_learning.conflict_detector import (
        detect_from_sqlite, summarize,
    )
    conflicts = detect_from_sqlite(workspace=args.workspace)
    s = summarize(conflicts)
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        if not conflicts:
            print("✅ 无冲突")
        else:
            for c in conflicts:
                print(f"  {c.to_line()}")
    return 0 if not conflicts else 1


def _cmd_inherit(args) -> int:
    from backend.agent_learning.rule_inheritance import merge_inherited
    r = merge_inherited(args.workspace)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"继承链 ({len(r['sources'])} 个 .rules):")
        for s in r["sources"]:
            print(f"  {s}")
        print(f"\n合并后 {r['rule_count']} 条规则:")
        for k, v in sorted(r["rules"].items()):
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
