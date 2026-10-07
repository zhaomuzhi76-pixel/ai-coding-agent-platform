from __future__ import annotations

from pathlib import Path

class PatchPathBoundary:
    """
    Resolve patch targets strictly inside a workspace root.

    Responsibility:
        - normalize patch-relative paths
        - reject absolute paths
        - reject traversal outside root
    """

    VERSION = "1.0"

    def resolve(
        self,
        root: str,
        file: str,
    ) -> Path:
        if not root:
            raise ValueError("patch root required")

        if not file:
            raise ValueError("patch file required")

        relative = Path(file)

        if relative.is_absolute():
            raise ValueError("absolute patch path forbidden")

        base = Path(root).resolve()
        target = (base / relative).resolve()

        if target != base and base not in target.parents:
            raise ValueError("patch path outside root")

        return target

    def resolve_snapshot(
        self,
        root: str,
        file: str,
    ) -> Path:
        if not root:
            raise ValueError("patch root required")
        if not file:
            raise ValueError("snapshot file required")

        base = Path(root).resolve()
        target = Path(file).expanduser().resolve()

        if target != base and base not in target.parents:
            raise ValueError("snapshot path outside root")

        return target

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

__all__ = [
    "PatchPathBoundary",
]
