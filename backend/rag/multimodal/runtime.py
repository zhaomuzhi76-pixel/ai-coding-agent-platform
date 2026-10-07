"""多模态 RAG 运行时（L2 依赖层，工厂 + Null 回退）。

职责：
- 单点入口 get_multimodal_rag_runtime()
- RAG_MULTIMODAL_ENABLED=1 → CLIP 真 runtime
- 否则 → Null Object（零依赖、无副作用）
真实现拆在 clip_runtime.py。
"""
from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)


# ---- Null Object 回退 ----

class _NullReply:
    hits: tuple = ()
    def __getattr__(self, name):
        return None


class _NullService:
    def search(self, *a, **k):
        return _NullReply()
    def __getattr__(self, name):
        return lambda *a, **k: None


class _NullRuntime:
    service = _NullService()
    def __getattr__(self, name):
        return _NullService()


_NULL = _NullRuntime()


# ---- 工厂 ----

def _enabled() -> bool:
    return os.environ.get("RAG_MULTIMODAL_ENABLED", "0") == "1"


def get_multimodal_rag_runtime(*args, **kwargs):
    if _enabled():
        try:
            from backend.rag.multimodal.clip_runtime import get_clip_runtime
            return get_clip_runtime()
        except Exception as e:
            logger.warning("[mm] CLIP runtime 加载失败，回退 Null: %r", e)
    return _NULL


def is_available() -> bool:
    if not _enabled():
        return False
    try:
        from backend.rag.multimodal.clip_runtime import is_clip_enabled
        return is_clip_enabled()
    except Exception:
        return False


def init_runtime(**kwargs):
    return None


def __getattr__(name: str):
    return None


__all__ = ["get_multimodal_rag_runtime", "is_available", "init_runtime"]
