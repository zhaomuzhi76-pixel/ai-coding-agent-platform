from __future__ import annotations

import re

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]")

_STOP = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "on",
    "is", "are", "be", "for", "with", "by", "as", "at",
    "这个", "那个", "的", "了", "是", "在", "和", "与",
})


def tokens(text: str) -> set[str]:
    if not isinstance(text, str):
        return set()
    return {
        t.lower()
        for t in _TOKEN.findall(text)
        if t.lower() not in _STOP
    }


def jaccard(a: str, b: str) -> float:
    ta = tokens(a)
    tb = tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


__all__ = ["tokens", "jaccard"]
