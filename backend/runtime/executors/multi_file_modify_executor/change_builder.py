"""Build per-file change entries by applying delta."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.runtime.executors.multi_file_modify_executor.delta_applier import (
    apply_delta,
)


def build_changes(
    loaded: List[Tuple[str, str]],
    delta: Dict[str, object],
    task: str,
) -> List[Dict[str, Any]]:
    changes: List[Dict[str, Any]] = []
    for rel, content in loaded:
        new_content = apply_delta(content, delta)
        if new_content == content:
            continue
        changes.append({
            "file": rel,
            "before": content,
            "after": new_content,
            "reason": task,
        })
    return changes
