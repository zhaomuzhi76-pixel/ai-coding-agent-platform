"""Part 1 of rag_tools.py."""
from __future__ import annotations

import asyncio

from backend.core.context.context_snapshot_contract import ContextSnapshot

from backend.core.tools.argument_contract import ToolArguments

from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)

from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol

from backend.core.tools.schema import ToolParameter, ToolSchema

from backend.rag.service import RagService

def _run(coro):
    """同步入口（tool runtime 是 async 的，但服务内部都 async）。"""
    return asyncio.get_event_loop().run_until_complete(coro)

class RagIndexDatasetTool(RuntimeToolProtocol):
    name = "rag_index_dataset"
    description = (
        "把 JSONL 数据集索引进 RAG 向量库（供后续检索使用）。"
        "参数：dataset_path = 绝对路径；dataset_id = 可选的 ID。"
    )
    VERSION = "1.0"

    def __init__(self, service: RagService) -> None:
        self._svc = service

    async def execute(self, arguments: ToolArguments) -> ToolResultProtocol:
        path = str(arguments.get("dataset_path", "") or "").strip()
        if not path:
            return ToolResult.success_result(
                self.name, {"error": "dataset_path required"},
            )
        ds_id = str(arguments.get("dataset_id", "") or "").strip()
        try:
            r = await self._svc.index_dataset(path, dataset_id=ds_id)
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
                    name="dataset_path", parameter_type="string",
                    description="JSONL 绝对路径",
                ),
                ToolParameter(
                    name="dataset_id", parameter_type="string",
                    description="可选，数据集 ID",
                    required=False,
                ),
            ),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {"name": self.name, "version": self.VERSION,
                "responsibility": "rag_index_dataset", "ready": self.ready()}

class RagQueryTool(RuntimeToolProtocol):
    name = "rag_query"
    description = (
        "在 RAG 向量库中检索最相关的片段。"
        "参数：query = 查询文本；top_k = 返回条数（默认 5）；"
        "use_rerank = 是否用 reranker 精排（默认 true）。"
    )
    VERSION = "1.0"

    def __init__(self, service: RagService) -> None:
        self._svc = service

    async def execute(self, arguments: ToolArguments) -> ToolResultProtocol:
        q = str(arguments.get("query", "") or "").strip()
        if not q:
            return ToolResult.success_result(
                self.name, {"error": "query required"},
            )
        top_k = int(arguments.get("top_k", 5) or 5)
        use_rerank = arguments.get("use_rerank", True)
        if isinstance(use_rerank, str):
            use_rerank = use_rerank.lower() in ("1", "true", "yes")
        try:
            hits = await self._svc.query_dict(
                q, top_k=top_k, use_rerank=bool(use_rerank),
            )
            return ToolResult.success_result(
                self.name, {"query": q, "count": len(hits), "hits": hits},
            )
        except Exception as exc:
            return ToolResult.success_result(
                self.name, {"error": f"{type(exc).__name__}: {exc}"},
            )

    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name, description=self.description,
            parameters=(
                ToolParameter(
                    name="query", parameter_type="string",
                    description="查询文本",
                ),
                ToolParameter(
                    name="top_k", parameter_type="integer",
                    description="返回条数（默认 5）", required=False,
                ),
                ToolParameter(
                    name="use_rerank", parameter_type="boolean",
                    description="是否精排（默认 true）", required=False,
                ),
            ),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {"name": self.name, "version": self.VERSION,
                "responsibility": "rag_query", "ready": self.ready()}

class RagStatusTool(RuntimeToolProtocol):
    name = "rag_status"
    description = "查询 RAG 索引状态：条数、collection、embedding、reranker 健康。"
    VERSION = "1.0"

    def __init__(self, service: RagService) -> None:
        self._svc = service

    async def execute(self, arguments: ToolArguments) -> ToolResultProtocol:
        try:
            st = await self._svc.status()
            return ToolResult.success_result(self.name, st)
        except Exception as exc:
            return ToolResult.success_result(
                self.name, {"error": f"{type(exc).__name__}: {exc}"},
            )

    def schema(self) -> ToolSchema:
        return ToolSchema(name=self.name, description=self.description)

    def ready(self) -> bool:
        return True

    def dump(self) -> ContextSnapshot:
        return {"name": self.name, "version": self.VERSION,
                "responsibility": "rag_status", "ready": self.ready()}
