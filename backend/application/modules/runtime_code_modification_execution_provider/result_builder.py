"""Build modification result payload."""
from __future__ import annotations

from typing import Callable


def build_result(
    file: str,
    kind: str,
    text: str,
    source: str,
    task: str,
    apply_kind: Callable[[str, str, str], str],
) -> dict:
    after = apply_kind(source, kind, text)
    return {
        "success": True,
        "file": file,
        "kind": kind,
        "text": text,
        "after": after,
        "changes": [{
            "file": file,
            "before": source,
            "after": after,
            "reason": task,
        }],
    }
