"""Part 2 of rag_tools.py."""
from __future__ import annotations
from .part1 import (ContextSnapshot, RagService, RuntimeToolProtocol, ToolArguments, ToolParameter, ToolResult, ToolResultProtocol, ToolSchema,)  # noqa
from .part1 import RagIndexDatasetTool  # noqa
from .part1 import RagQueryTool  # noqa
from .part1 import RagStatusTool  # noqa

class RagClearTool(RuntimeToolProtocol):
    name = "rag_clear"
    description = "清空 RAG 索引（危险操作，仅用于重建）。"
    VERSION = "1.0"

    def __init__(self, service: RagService) -> None:
        self._svc = service

    async def execute(self, arguments: ToolArguments) -> ToolResultProtocol:
        confirm = arguments.get("confirm", False)
        if isinstance(confirm, str):
            confirm = confirm.lower() in ("1", "true", "yes")
        if not confirm:
            return ToolResult.success_result(
                self.name, {"error": "confirm=true required"},
            )
        try:
            r = self._svc.clear()
            return ToolResult.success_result(self.name, r)
        except Exception as exc:
            return ToolResult.success_result(
                self.name, {"error": f"{type(exc).__name__}: {exc}"},
            )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name, description=self.description,
            parameters=(
                ToolParameter(
                    name="confirm", parameter_type="boolean",
                    description="必须为 true 才执行",
                ),
            ),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {"name": self.name, "version": self.VERSION,
                "responsibility": "rag_clear", "ready": self.ready()}

class RagIndexAllFinetuneTool(RuntimeToolProtocol):
    name = "rag_index_all_finetune_datasets"
    description = (
        "一键把所有微调数据集索引进 RAG 向量库（幂等，"
        "重复调用不膨胀）。索引后可用 rag_query 检索。"
    )
    VERSION = "1.0"

    def __init__(self, service: RagService) -> None:
        self._svc = service

    async def execute(self, arguments: ToolArguments) -> ToolResultProtocol:
        try:
            from backend.finetune.dataset.manager import get_dataset_manager
            mgr = get_dataset_manager()
            rows = mgr.list(limit=1000) or []
            total = 0
            details = []
            for r in rows:
                path = str(r.get("path", "") or "")
                ds_id = str(r.get("dataset_id", "") or "")
                if not path:
                    continue
                try:
                    rep = await self._svc.index_dataset(path, dataset_id=ds_id)
                    n = int(rep.get("indexed", 0) or 0)
                    total += n
                    details.append({"dataset_id": ds_id, "indexed": n})
                except Exception as exc:
                    details.append({
                        "dataset_id": ds_id,
                        "error": f"{type(exc).__name__}: {exc}"[:120],
                    })
            return ToolResult.success_result(self.name, {
                "total_indexed": total,
                "dataset_count": len(rows),
                "collection_total": self._svc.count(),
                "details": details,
            })
        except Exception as exc:
            return ToolResult.success_result(
                self.name, {"error": f"{type(exc).__name__}: {exc}"},
            )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name, description=self.description,
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {"name": self.name, "version": self.VERSION,
                "responsibility": "rag_index_all_finetune", "ready": self.ready()}

def build_rag_tools(service: RagService) -> list:
    """构造 4 个 RAG 工具（不改任何全局状态）。"""
    return [
        RagIndexDatasetTool(service),
        RagIndexAllFinetuneTool(service),
        RagQueryTool(service),
        RagStatusTool(service),
        RagClearTool(service),
    ]

def register_rag_tools(tool_runtime, service: RagService) -> list:
    """注册到 ToolRuntime。返回注册的工具名列表。"""
    names = []
    for tool in build_rag_tools(service):
        tool_runtime.register_tool(tool)
        names.append(tool.name)
    return names

__all__ = [
    "RagIndexDatasetTool", "RagQueryTool",
    "RagStatusTool", "RagClearTool", "RagIndexAllFinetuneTool",
    "build_rag_tools", "register_rag_tools",
]
