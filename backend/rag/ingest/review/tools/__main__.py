"""L23 工具 CLI：gate / fix / test / probe / smoke（返回退出码，不主动退出终端）。"""
from __future__ import annotations

import argparse
import json
import sys


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="review-tools", add_help=True)
    sub = p.add_subparsers(dest="cmd")

    g = sub.add_parser("gate", help="分层审查")
    g.add_argument("--layer", action="append", default=[])
    g.add_argument("--all", action="store_true")
    g.add_argument("--output", default="")

    f = sub.add_parser("fix", help="分层修复")
    f.add_argument("--scope", default="backend/rag/ingest/review")
    f.add_argument("--from-report", dest="report", default="")

    t = sub.add_parser("test", help="无痕测试")
    t.add_argument("--layer", action="append", default=[])
    t.add_argument("--all", action="store_true")

    pr = sub.add_parser("probe", help="探测现有后端真实接口（AST，不 import）")
    pr.add_argument("--target", action="append", default=[])
    pr.add_argument("--all", action="store_true")

    sm = sub.add_parser("smoke", help="端到端冒烟（真实后端）")

    df = sub.add_parser("dify", help="Dify 工作流导出/校验")
    df.add_argument("action", choices=["export", "check"])
    df.add_argument("--output", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.cmd == "gate":
        from backend.rag.ingest.review.tools import gate
        layers = [] if args.all else args.layer
        result = gate.run_gate(layers, args.output or None)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1
    if args.cmd == "fix":
        from backend.rag.ingest.review.tools import fix
        result = fix.run_fix(args.scope, args.report or None)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.cmd == "test":
        from backend.rag.ingest.review.tools import ephemeral
        layers = [] if args.all else args.layer
        result = ephemeral.run_ephemeral(layers)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1
    if args.cmd == "probe":
        from backend.rag.ingest.review.tools import probe
        targets = [] if args.all else args.target
        report = probe.probe_all(targets or None)
        print(probe.render(report))
        return 0
    if args.cmd == "smoke":
        from backend.rag.ingest.review.tools import smoke
        result = smoke.run_smoke()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1
    if args.cmd == "dify":
        from backend.rag.ingest.review.tools import dify_cli
        result = dify_cli.run_dify(args.action, args.output or None)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1
    _parser().print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
