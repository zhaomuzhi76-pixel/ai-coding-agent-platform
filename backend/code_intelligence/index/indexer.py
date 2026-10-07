from __future__ import annotations

from pathlib import Path

class CodeIndexer:
    """
    Industrial repository indexer.

    Responsibility:
        - discover source files
        - provide normalized file inventory

    Not Responsible:
        - parsing
        - embedding
        - persistence
    """

    VERSION = "1.1"

    RESPONSIBILITY = (
        "industrial_code_indexer"
    )

    def __init__(
        self,
        workspace: str,
    ) -> None:
        self.workspace = Path(workspace)

    def scan_files(self) -> list[str]:
        if not self.workspace.exists():
            return []

        return sorted(
            str(item.relative_to(self.workspace))
            for item in self.workspace.rglob("*.py")
        )

    def build_index(self) -> list[dict[str, str]]:
        return [
            {"path": path}
            for path in self.scan_files()
        ]

    def ready(self) -> bool:
        return self.workspace.exists()

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "workspace": str(self.workspace),
            "ready": self.ready(),
        }

__all__ = [
    "CodeIndexer",
]
