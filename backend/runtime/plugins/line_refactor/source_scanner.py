"""扫描超限 Python 文件。"""
from __future__ import annotations

import os
from typing import Iterator, List, Tuple


def iter_python_files(root: str) -> Iterator[str]:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def count_lines(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def load_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def find_oversized(root: str, limit: int) -> List[Tuple[str, int]]:
    result: List[Tuple[str, int]] = []
    for path in iter_python_files(root):
        n = count_lines(path)
        if n > limit:
            result.append((path, n))
    return result
