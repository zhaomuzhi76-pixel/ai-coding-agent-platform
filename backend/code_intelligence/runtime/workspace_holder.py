from __future__ import annotations

import threading
from typing import Any

from backend.code_intelligence.composition import (
    CodeIntelligenceComposition,
)


class WorkspaceHolder:
    """
    Global single-flight holder for a workspace's code intelligence.

    Responsibility:
        - lazily construct CodeIntelligenceWorkspace per root path
        - cache the workspace so index/graph is built only once
        - thread-safe lookup

    Not responsible:
        - index construction (that is CodeIntelligenceComposition)
        - symbol retrieval
        - code modification
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[str, Any] = {}
        self._index_cache: dict[str, list[dict[str, Any]]] = {}

    def get(self, workspace: str) -> Any:
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("workspace required")

        key = workspace.strip()
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached

            composition = CodeIntelligenceComposition(workspace=key)
            workspace_obj = composition.create()

            # 立即建索引，缓存在 holder 里，避免每次查都重扫
            try:
                index = workspace_obj.build_index()
            except Exception as error:
                raise RuntimeError(
                    f"failed to build index for {key}: {error}"
                ) from error

            print(
                f"[workspace-holder] indexed {key} "
                f"({len(index)} files)",
                flush=True,
            )

            self._cache[key] = workspace_obj
            self._index_cache[key] = index
            return workspace_obj

    def get_index(self, workspace: str) -> list[dict[str, Any]]:
        # 触发 get() 保证 index 已建
        self.get(workspace)
        return self._index_cache.get(workspace.strip(), [])

    def invalidate(self, workspace: str) -> None:
        key = workspace.strip()
        with self._lock:
            self._cache.pop(key, None)
            self._index_cache.pop(key, None)

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "cached_workspaces": list(self._cache.keys()),
        }


# ── module-level singleton ──────────────────────────────
_HOLDER: WorkspaceHolder | None = None
_HOLDER_LOCK = threading.Lock()


def get_workspace_holder() -> WorkspaceHolder:
    global _HOLDER
    if _HOLDER is None:
        with _HOLDER_LOCK:
            if _HOLDER is None:
                _HOLDER = WorkspaceHolder()
    return _HOLDER


def reset_workspace_holder() -> None:
    global _HOLDER
    with _HOLDER_LOCK:
        _HOLDER = None


__all__ = [
    "WorkspaceHolder",
    "get_workspace_holder",
    "reset_workspace_holder",
]
