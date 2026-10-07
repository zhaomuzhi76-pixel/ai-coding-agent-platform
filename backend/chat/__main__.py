"""CLI: python -m backend.chat seed <domain> | list"""
from __future__ import annotations

import argparse
import json
import sys


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="chat")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("seed", help="索引领域数据 + 图 URL")
    s.add_argument("domain", help="agriculture / finance")
    s.add_argument("--json", action="store_true")
    sub.add_parser("list", help="列出可索引领域")
    return p


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.cmd == "seed":
        from backend.chat.domain_seeder import seed_domain
        result = seed_domain(args.domain)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"✅ {result}")
        return 0 if result.get("status") == "ok" else 1
    if args.cmd == "list":
        from backend.chat.domain_seeder import IMAGE_URLS
        print(f"可索引领域: {sorted(IMAGE_URLS.keys())}")
        return 0
    _parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
