"""Resolve project workspace runtime binding."""
from __future__ import annotations

from backend.api.project.project_registration_api import (
    ProjectRegistrationAPI,
)
from backend.api.project.project_workspace_router_support.errors import (
    WorkspaceResourceError,
)
from backend.workspace.runtime_binding import WorkspaceRuntimeBinding


# 进程内 binding 缓存（key=root_path）。
# 首次扫描 2s+，之后 0ms。
# 4 个调用点（tree/file/write/support）只用 get_filesystem()（实时读盘），
# 不依赖 index 的新鲜度，所以缓存安全。
# 需要失效时调 invalidate_workspace(root_path)。
_binding_cache: dict[str, WorkspaceRuntimeBinding] = {}


async def resolve_workspace(
    api: ProjectRegistrationAPI,
    project_id: str,
) -> WorkspaceRuntimeBinding:
    result = api.get(project_id)
    if hasattr(result, "__await__"):
        result = await result
    root_path = getattr(result, "root_path", None)
    if not isinstance(root_path, str) or not root_path.strip():
        raise WorkspaceResourceError("project root_path unavailable")

    cached = _binding_cache.get(root_path)
    if cached is not None:
        return cached

    binding = WorkspaceRuntimeBinding(root_path=root_path)
    _binding_cache[root_path] = binding
    return binding


def invalidate_workspace(root_path: str) -> None:
    """手动失效（用于文件结构大改 / 换项目）。"""
    _binding_cache.pop(root_path, None)


def cache_stats() -> dict:
    return {
        "size": len(_binding_cache),
        "roots": list(_binding_cache.keys()),
    }
