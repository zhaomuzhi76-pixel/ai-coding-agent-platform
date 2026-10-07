"""目录扫描器。"""
from __future__ import annotations

import os
from typing import Iterator

from backend.runtime.plugins.layer_audit.audit_models import FileProfile
from backend.runtime.plugins.layer_audit.file_profiler import profile


_SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}


def iter_py(root: str) -> Iterator[str]:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def scan(root: str) -> list:
    profiles = []
    for path in iter_py(root):
        try:
            profiles.append(profile(path, root))
        except (SyntaxError, OSError):
            continue
    return profiles


def scan_paths(paths: list, root: str) -> list:
    """支持显式路径列表（用于跨层审查）。"""
    result = []
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            result.append(profile(path, root))
        except (SyntaxError, OSError):
            continue
    return result
