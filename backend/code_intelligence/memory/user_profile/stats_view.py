"""Stats view for user profile."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from backend.code_intelligence.memory._shared.stats import count_rows


def stats(db_path: Path) -> Dict[str, Any]:
    return {
        "observations": count_rows(db_path, "observations"),
        "preferences": count_rows(db_path, "preferences"),
        "db": str(db_path),
    }
