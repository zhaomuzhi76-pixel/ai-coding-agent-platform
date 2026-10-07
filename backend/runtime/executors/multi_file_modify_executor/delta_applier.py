"""Apply a delta to arbitrary file content."""
from __future__ import annotations

from typing import Dict


def apply_delta(content: str, delta: Dict[str, object]) -> str:
    kind = delta.get("kind")
    text = delta.get("text", "")
    if kind == "prepend":
        return str(text) + content
    if kind == "append":
        return content + str(text)
    if kind == "insert_after_line":
        after_line = delta.get("after_line", 0)
        if not isinstance(after_line, int) or after_line < 0:
            raise ValueError("insert_after_line requires int")
        lines = content.split("\n")
        idx = min(after_line, len(lines))
        lines.insert(idx, str(text))
        return "\n".join(lines)
    raise ValueError(f"unsupported delta kind: {kind}")
