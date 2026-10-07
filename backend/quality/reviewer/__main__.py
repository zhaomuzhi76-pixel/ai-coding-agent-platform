"""CLI: python -m backend.quality.reviewer <root>"""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="reviewer")
    p.add_argument("root")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    from backend.quality.reviewer.runner import review
    return review(args.root, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
