"""RAG tools（4 个 RuntimeToolProtocol 实现）。

工具：
    - rag_index_dataset  从 JSONL 数据集文件索引
    - rag_query          向量检索 + reranker 精排
    - rag_status         索引统计 + 健康
    - rag_clear          清空索引（危险）

职责：
    - 把 RagService 的能力暴露为工具协议
    - 参数校验 + 结果包装

不负责：
    - RAG 核心逻辑（service / indexer / retriever 管）
    - MCP 协议（server / bridge 管）
\n\nCompat shim. See ._rag_tools_parts."""
from __future__ import annotations
from ._rag_tools_parts import *  # noqa
from ._rag_tools_parts import (ContextSnapshot, RagClearTool, RagIndexAllFinetuneTool, RagIndexDatasetTool, RagQueryTool, RagService, RagStatusTool, RuntimeToolProtocol, ToolArguments, ToolParameter, ToolResult, ToolResultProtocol, ToolSchema, __all__, _run, annotations, asyncio, build_rag_tools, register_rag_tools,)  # noqa
