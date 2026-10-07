"""从 ExecutionNode 提取 code modification 请求数据。"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol

from backend.runtime.executors.code_modify_executor.contract import RequestData


def _extract_arguments(tool_call: Any) -> Dict[str, Any]:
    if isinstance(tool_call, dict):
        args = tool_call.get("arguments", {})
        return args if isinstance(args, dict) else {}
    return {}


def _extract_task(parameters: Dict[str, Any],
                  arguments: Dict[str, Any]) -> str:
    task = parameters.get("task") or parameters.get("message", "")
    if not task:
        task = arguments.get("instruction", "")
    return task


def _extract_files(parameters: Dict[str, Any],
                   arguments: Dict[str, Any]) -> List[Any]:
    files = parameters.get("files", [])
    path = arguments.get("path")
    if not files and isinstance(path, str) and path:
        return [path]
    return files


def _extract_changes(parameters: Dict[str, Any],
                     context: KernelContext) -> Optional[Dict[str, Any]]:
    changes = parameters.get("changes")
    if changes is None:
        changes = context.get("changes")
    return changes


def extract_request(node: ExecutionNodeProtocol,
                    context: KernelContext,
                    workspace_root: str) -> RequestData:
    parameters = node.parameters
    arguments = _extract_arguments(parameters.get("tool_call", {}))
    return RequestData(
        task=_extract_task(parameters, arguments),
        files=_extract_files(parameters, arguments),
        source=arguments.get("content"),
        instruction=arguments.get("instruction", ""),
        changes=_extract_changes(parameters, context),
        path=arguments.get("path"),
        workspace_root=workspace_root,
    )
