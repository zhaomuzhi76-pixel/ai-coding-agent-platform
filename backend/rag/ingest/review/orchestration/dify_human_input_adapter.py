"""L4 Dify Human Input 节点适配器 —— 导出/导入工作流 JSON。"""
from __future__ import annotations

from typing import Any

WORKFLOW_NODES = (
    {"id": "upload", "type": "start", "desc": "用户上传文档"},
    {"id": "parse", "type": "code", "desc": "L1 解析器"},
    {"id": "chunk", "type": "code", "desc": "L1 分块器"},
    {"id": "save_draft", "type": "code",
     "desc": "L2 保存草稿 → pending_review"},
    {"id": "recall_preview", "type": "code",
     "desc": "L3 可视化召回 BM25+Reranker"},
    {"id": "human_review", "type": "human_input", "desc": "人工审核草稿",
     "config": {
         "form_fields": [
             {"name": "chunk_preview", "type": "json"},
             {"name": "recall_result", "type": "json"},
             {"name": "edits", "type": "textarea"},
         ],
         "actions": ["approve", "reject", "edit_and_approve"],
     }},
    {"id": "promote", "type": "code", "desc": "L2 写入向量库 → done"},
    {"id": "cleanup", "type": "code", "desc": "拒绝时清理草稿 → rejected"},
)

EDGES = (
    ("upload", "parse"),
    ("parse", "chunk"),
    ("chunk", "save_draft"),
    ("save_draft", "recall_preview"),
    ("recall_preview", "human_review"),
    ("human_review", "promote"),
    ("human_review", "cleanup"),
)


def export_workflow() -> dict[str, Any]:
    return {"nodes": list(WORKFLOW_NODES), "edges": list(EDGES)}
