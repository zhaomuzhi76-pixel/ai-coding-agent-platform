"""L3 Dify 工作流构建器 —— 生成可导入 Workflow Studio 的 JSON。"""
from __future__ import annotations

from typing import Any

WORKFLOW_NAME = "RAG 审核门（两阶段入库）"
WORKFLOW_DESC = "上传→解析→分块→草稿→可视化召回→Human Input 审核→写入向量库"

_NODE_DEFS: tuple[tuple[str, str, str, int, int], ...] = (
    ("upload",         "start",        "上传文档",            80,   80),
    ("parse",          "code",         "L1 解析器",          380,   80),
    ("chunk",          "code",         "L1 分块器",          680,   80),
    ("save_draft",     "code",         "L2 写草稿",          980,   80),
    ("recall_preview", "code",         "L3 可视化召回",      1280,  80),
    ("human_review",   "human-input",  "人工审核草稿",        1580,  80),
    ("promote",        "code",         "L2 写入向量库",      1880,  80),
    ("cleanup",        "code",         "拒绝清理草稿",        1880, 320),
    ("end",            "end",          "结束",              2180,  80),
)

_EDGES: tuple[tuple[str, str], ...] = (
    ("upload", "parse"),
    ("parse", "chunk"),
    ("chunk", "save_draft"),
    ("save_draft", "recall_preview"),
    ("recall_preview", "human_review"),
    ("human_review", "promote"),
    ("human_review", "cleanup"),
    ("promote", "end"),
    ("cleanup", "end"),
)

_HUMAN_FORM: tuple[dict[str, Any], ...] = (
    {"type": "paragraph", "variable": "chunk_preview_json",
     "label": "草稿块与召回打分", "required": False, "max_length": 20000},
    {"type": "paragraph", "variable": "edits_json",
     "label": "编辑后的草稿块", "required": False, "max_length": 20000},
    {"type": "paragraph", "variable": "approved_chunk_ids",
     "label": "通过的块 ID（逗号分隔）", "required": False, "max_length": 2000},
)

_HUMAN_ACTIONS: tuple[dict[str, str], ...] = (
    {"id": "approve", "title": "全部通过", "button_style": "primary"},
    {"id": "edit_and_approve", "title": "编辑后通过", "button_style": "default"},
    {"id": "reject", "title": "拒绝全部", "button_style": "danger"},
)


def build_workflow() -> dict[str, Any]:
    nodes = [_node(nid, ntype, title, x, y)
             for nid, ntype, title, x, y in _NODE_DEFS]
    edges = [_edge(src, dst) for src, dst in _EDGES]
    return {
        "app": {
            "name": WORKFLOW_NAME, "mode": "workflow",
            "icon": "🗂️", "icon_background": "#EFF1F5",
            "description": WORKFLOW_DESC,
        },
        "workflow": {
            "graph": {
                "nodes": nodes, "edges": edges,
                "viewport": {"x": 0, "y": 0, "zoom": 0.7},
            },
            "features": {"file_upload": {"enabled": True,
                                          "allowed_file_types": [".txt", ".md", ".pdf"]}},
            "environment_variables": [],
            "conversation_variables": [],
        },
    }


def _node(node_id: str, node_type: str, title: str,
          x: int, y: int) -> dict[str, Any]:
    data: dict[str, Any] = {"type": node_type, "title": title, "desc": ""}
    if node_type == "human-input":
        data["form_fields"] = [dict(f) for f in _HUMAN_FORM]
        data["actions"] = [dict(a) for a in _HUMAN_ACTIONS]
    elif node_type == "code":
        data["code_language"] = "python3"
        data["code"] = f"# L23 节点 {node_id}\nreturn {{'ok': True}}\n"
        data["variables"] = []
    return {
        "id": node_id, "type": node_type, "data": data,
        "position": {"x": x, "y": y},
        "width": 244, "height": 100 if node_type != "human-input" else 160,
    }


def _edge(source: str, target: str) -> dict[str, Any]:
    return {
        "id": f"e-{source}-{target}",
        "source": source, "target": target,
        "sourceHandle": "source", "targetHandle": "target",
        "type": "custom", "data": {"isInIteration": False},
    }
