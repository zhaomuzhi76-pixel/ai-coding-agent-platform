"""PlatformPipeline 的 I/O 辅助：事件发射 + 主文件读取。

职责：
  - 统一事件发射（含异常吞没）
  - 读取 primary file（复用 L0 路径权威）
不负责：
  - 提案构造
  - 阶段推进
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any, Optional


async def emit_event(
    events: Any,
    event_callback: Optional[Any],
    event: Any,
) -> None:
    """统一事件发射。任何通道失败都静默（不阻塞 pipeline）。"""
    try:
        if event_callback is not None:
            await event_callback(event)
        else:
            events.emit(event)
    except Exception as e:
        swallow("platform.pipeline_io:28", e, level="warn")


def read_primary(
    workspace: str, rel_path: str, *, allow_missing: bool = False,
) -> str:
    """读取 primary file（复用 L0 文件操作）。

    allow_missing=True 时，文件不存在返回空字符串（用于"新建文件"场景）。
    其它 I/O 错误（权限等）仍抛出，不静默吞掉。
    """
    from backend.workspace.file_ops import exists, read_text
    try:
        return read_text(workspace, rel_path)
    except (FileNotFoundError, OSError) as exc:
        if allow_missing and not exists(workspace, rel_path):
            return ""
        raise
    except Exception:
        if allow_missing and not exists(workspace, rel_path):
            return ""
        raise


__all__ = ["emit_event", "read_primary"]
