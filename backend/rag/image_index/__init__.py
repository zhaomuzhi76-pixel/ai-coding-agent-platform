from backend.rag.image_index.contracts import (
    ImageVector, ImageSearchHit, ImageSearchReport, SearchMode)
# [MERGE] 从 multimodal.clip_embedder 导入（兼容层）
from backend.rag.multimodal.clip_embedder import (
    ClipEmbedder as ClipEngine,
    get_embedder as get_default_clip_engine,
)

def make_clip_engine(*, model_name: str = "", device: str = "") -> ClipEngine:
    """兼容工厂：忽略参数，返回全局单例。"""
    return get_default_clip_engine()

def set_default_clip_engine(e) -> None:
    """兼容接口：交给 multimodal.clip_embedder 的 _singleton。"""
    from backend.rag.multimodal import clip_embedder as _ce
    _ce._singleton = e
from backend.rag.image_index.store import (
    ImageVectorStore, get_default_image_store,
    set_default_image_store)
from backend.rag.image_index.indexer import (
    ImageIndexer, ImageIndexReport, make_image_indexer)
from backend.rag.image_index.retriever import (
    ImageRetriever, make_image_retriever)

__all__ = ["ImageVector", "ImageSearchHit",
           "ImageSearchReport", "SearchMode",
           "ClipEngine", "make_clip_engine",
           "get_default_clip_engine", "set_default_clip_engine",
           "ImageVectorStore", "get_default_image_store",
           "set_default_image_store",
           "ImageIndexer", "ImageIndexReport", "make_image_indexer",
           "ImageRetriever", "make_image_retriever"]
