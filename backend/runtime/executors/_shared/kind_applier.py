"""Apply patch kind (prepend/append/replace_all) to source."""
from __future__ import annotations


def apply_kind(source: str, kind: str, text: str) -> str:
    if kind == "prepend":
        return text + "\n" + source
    if kind == "append":
        if source and not source.endswith("\n"):
            return source + "\n" + text
        return source + text
    if kind == "replace_all":
        return text
    raise ValueError(f"unsupported kind: {kind}")
