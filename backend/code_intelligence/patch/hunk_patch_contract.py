from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hunk:
    """单个 search-replace 操作。"""
    old_string: str
    new_string: str

    def ready(self) -> bool:
        return (
            isinstance(self.old_string, str)
            and isinstance(self.new_string, str)
            and bool(self.old_string)
            and self.old_string != self.new_string
        )

    def dump(self) -> dict[str, Any]:
        return {
            "old_string": self.old_string,
            "new_string": self.new_string,
        }


@dataclass
class FileChange:
    """一个文件的所有 hunk。"""
    file: str
    hunks: list[Hunk] = field(default_factory=list)

    def ready(self) -> bool:
        return (
            isinstance(self.file, str)
            and bool(self.file.strip())
            and bool(self.hunks)
            and all(h.ready() for h in self.hunks)
        )

    def dump(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "hunks": [h.dump() for h in self.hunks],
        }


@dataclass
class HunkPatch:
    """一次修改涉及的所有文件变更。"""
    changes: list[FileChange] = field(default_factory=list)

    def ready(self) -> bool:
        return bool(self.changes) and all(
            c.ready() for c in self.changes
        )

    def files(self) -> list[str]:
        return [c.file for c in self.changes]

    def dump(self) -> dict[str, Any]:
        return {
            "changes": [c.dump() for c in self.changes],
        }


# ─── Schema（供 LLM prompt 引用） ────────────────────────
HUNK_PATCH_SCHEMA_EXAMPLE = '''{
  "changes": [
    {
      "file": "relative/path.py",
      "hunks": [
        {
          "old_string": "<exact source text, verbatim>",
          "new_string": "<replacement text>"
        }
      ]
    }
  ]
}'''


__all__ = [
    "Hunk",
    "FileChange",
    "HunkPatch",
    "HUNK_PATCH_SCHEMA_EXAMPLE",
]
