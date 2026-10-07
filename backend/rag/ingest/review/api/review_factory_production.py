"""L4 生产装配 —— 真实后端优先，AST + import 双探测，缺失优雅回落。"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Any

from backend.rag.ingest.review.api.review_router import ReviewApi
from backend.rag.ingest.review.review.approval_router import ApprovalRouter
from backend.rag.ingest.review.review.bm25_scorer_adapter import build_scorer
from backend.rag.ingest.review.review.draft_state_machine import DraftStateMachine
from backend.rag.ingest.review.review.recall_visualizer import RecallVisualizer
from backend.rag.ingest.review.review.reranker_adapter import build_reranker
from backend.rag.ingest.review.storage.draft_promoter import DraftPromoter
from backend.rag.ingest.review.storage.draft_store import get_default_draft_store
from backend.rag.ingest.review.storage.vector_writer_adapter import build_writer

_GATE_FILE = "backend/quality/layer_dependency_gate.py"
_GATE_MODULE = "backend.quality.layer_dependency_gate"
_GATE_CLASS = "LayerDependencyGate"


def build_production_api(
    writer: Any | None = None,
    bm25: Any | None = None,
    reranker: Any | None = None,
) -> ReviewApi:
    store = get_default_draft_store()
    machine = DraftStateMachine()
    real_writer = writer if writer is not None else build_writer()
    promoter = DraftPromoter(store, real_writer)
    visualizer = RecallVisualizer(
        bm25 if bm25 is not None else build_scorer(),
        reranker if reranker is not None else build_reranker(),
    )
    return ReviewApi(ApprovalRouter(store, machine, promoter), visualizer)


def gate_backend() -> str:
    """4 状态：existing / existing-broken / self / missing。

    不 import，仅 AST 确认 class 存在；再尝试 import 一次判定健康度。
    """
    path = Path(_GATE_FILE)
    if not path.exists():
        return "missing"
    if not _has_class(path, _GATE_CLASS):
        return "self"
    try:
        importlib.import_module(_GATE_MODULE)
        return "existing"
    except Exception:
        return "existing-broken"


def backends() -> dict[str, str]:
    return {
        "writer": _safe(build_writer),
        "bm25": _safe(build_scorer),
        "reranker": _safe(build_reranker),
        "gate": gate_backend(),
    }


def _safe(factory) -> str:
    try:
        return factory().backend
    except Exception:
        return "fallback"


def _has_class(path: Path, name: str) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return False
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return True
    return False
