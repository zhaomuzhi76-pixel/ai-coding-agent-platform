"""_apply_recall_config — 从 retriever.py 抽出。"""
from __future__ import annotations


def _apply_recall_config(top_k: int, use_rerank):
    """惰性读全局配置：面板改参数后主检索立即生效。
    优先级：显式传参 > 全局配置 > 默认值。"""
    try:
        from backend.rag.recall_config import get_default_config
        cfg = get_default_config().get()
    except Exception:
        return top_k, use_rerank
    # top_k=5 视为默认未传；配置值覆盖
    if top_k == 5 and cfg.top_k != 5:
        top_k = cfg.top_k
    if use_rerank is None:
        use_rerank = cfg.use_reranker
    return top_k, use_rerank
