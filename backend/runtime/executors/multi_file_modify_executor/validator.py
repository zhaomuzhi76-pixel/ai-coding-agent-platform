"""Input validation + root resolution."""
from __future__ import annotations

from typing import Any

from backend.application.planning.workspace_path_normalizer import (
    normalize_workspace_path,
)


def validate_inputs(files: Any, task: Any) -> None:
    if not isinstance(files, list) or not files:
        raise ValueError("multi_file_modify files required")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("multi_file_modify task required")


def resolve_root(context: Any) -> str:
    root = getattr(context, "workspace_id", None)
    if not isinstance(root, str) or not root.strip():
        root = context.get("root")
    if not isinstance(root, str) or not root.strip():
        raise RuntimeError("multi_file_modify workspace_id required")
    return normalize_workspace_path(root)
