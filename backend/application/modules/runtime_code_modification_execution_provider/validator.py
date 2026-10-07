"""Validate modification request payload."""
from __future__ import annotations


def validate_request(task: str, files: list, context: dict) -> str:
    if not isinstance(task, str) or not task.strip():
        raise ValueError("modification task required")
    if not isinstance(files, list) or len(files) != 1:
        raise ValueError("code modification requires exactly one file")
    file = files[0]
    if not isinstance(file, str) or not file.strip():
        raise ValueError("modification file required")
    if not isinstance(context, dict):
        raise TypeError("modification context must dict")
    if not isinstance(context.get("source"), str):
        raise ValueError("source content required for code modification")
    return file.strip()
