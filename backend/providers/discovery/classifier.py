"""模型分类器：识别 embedding / reranker，无硬编码模型名。

识别规则（可扩展）：
  - 名字含 -embedding / :embed / bge- / nomic-embed / gte- / e5-
  - details.family 含 bert / nomic-bert / mxbai
  - 名字含 reranker / -rerank
"""
from __future__ import annotations

_EMBEDDING_NAME_HINTS = (
    "-embedding", ":embedding",
    "-embed:", ":embed:",
    "bge-", "bge:",
    "nomic-embed", "mxbai-embed",
    "gte-", "gte:",
    "e5-", "e5:",
    "text-embedding",
)

_EMBEDDING_FAMILIES = (
    "bert", "nomic-bert", "mxbai",
)

_RERANKER_HINTS = ("reranker", "-rerank", ":rerank")


def is_embedding_model(
    name: str, details: dict | None = None,
) -> bool:
    n = (name or "").lower()
    if any(h in n for h in _EMBEDDING_NAME_HINTS):
        return True
    if details:
        fam = str(details.get("family", "")).lower()
        if any(f in fam for f in _EMBEDDING_FAMILIES):
            return True
    return False


def is_reranker_model(name: str) -> bool:
    n = (name or "").lower()
    return any(h in n for h in _RERANKER_HINTS)


def should_include_as_chat(
    name: str, details: dict | None = None,
) -> bool:
    """chat 模型过滤：排除 embedding 和 reranker。"""
    if not (name or "").strip():
        return False
    if is_embedding_model(name, details):
        return False
    if is_reranker_model(name):
        return False
    return True


__all__ = [
    "is_embedding_model",
    "is_reranker_model",
    "should_include_as_chat",
]
