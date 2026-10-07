"""Load non-empty files from workspace."""
from __future__ import annotations

import os
from typing import Any, List, Tuple


def load_files(root: str, files: Any) -> List[Tuple[str, str]]:
    loaded: List[Tuple[str, str]] = []
    for rel in files:
        if not isinstance(rel, str):
            continue
        abs_path = rel if os.path.isabs(rel) else os.path.join(root, rel)
        try:
            with open(abs_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except OSError:
            continue
        if content:
            loaded.append((rel, content))
    return loaded
