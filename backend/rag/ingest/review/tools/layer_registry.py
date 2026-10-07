"""L23 层清单（纯数据，单一职责）。"""
from __future__ import annotations

#: 自下而上的层序：越靠下越基础，上层可依赖下层，下层禁止依赖上层。
LAYERS: tuple[tuple[str, str], ...] = (
    ("foundation", "backend.rag.ingest.review.foundation"),
    ("storage", "backend.rag.ingest.review.storage"),
    ("review", "backend.rag.ingest.review.review"),
    ("api", "backend.rag.ingest.review.api"),
    ("orchestration", "backend.rag.ingest.review.orchestration"),
)
LAYER_NAMES: tuple[str, ...] = tuple(n for n, _ in LAYERS)
LAYER_ORDER: dict[str, int] = {n: i for i, n in enumerate(LAYER_NAMES)}
REVIEW_PREFIX = "backend.rag.ingest.review."
REPORT_DIR = ".layer-review"
MAX_LINES = 230


def module_of(name: str) -> str:
    for n, m in LAYERS:
        if n == name:
            return m
    raise KeyError(f"unknown layer: {name}")


def module_path(module: str) -> str:
    return module.replace(".", "/")


def report_path(layer: str) -> str:
    return f"{REPORT_DIR}/{layer}-latest.json"
