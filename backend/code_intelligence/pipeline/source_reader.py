from __future__ import annotations

from pathlib import Path

class SourceReader:
    """
    Source file reader.

    Responsibility:
        - read source files

    Not Responsible:
        - parsing
        - chunk generation
        - indexing
    """

    def read(
        self,
        path: Path,
    ) -> str:
        return path.read_text(
            encoding="utf-8"
        )

__all__ = [
    "SourceReader",
]
