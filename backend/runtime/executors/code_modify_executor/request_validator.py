"""校验提取后的请求数据，保持与原实现一致。"""
from __future__ import annotations

from backend.runtime.executors.code_modify_executor.contract import RequestData


def validate_request(req: RequestData) -> None:
    if not isinstance(req.workspace_root, str) or not req.workspace_root.strip():
        raise RuntimeError("runtime context workspace_id required")
    if not isinstance(req.task, str) or not req.task.strip():
        raise ValueError("modification task required")
    if not isinstance(req.files, list) or not req.files:
        raise ValueError("modification files required")
    if not isinstance(req.source, str):
        raise ValueError("source content required")
    if req.changes is not None and not isinstance(req.changes, dict):
        raise TypeError("modification changes must dict")
