"""中文文本编码器（工业级插件）。

职责：给多模态融合提供统一的文本 embedding 接口。
  - 优先复用现有 RAG 文本 embed（不引入重复）
  - 无现有 embed 时回退 BGE 中文模型
不做：不存储、不检索、不做 RRF。
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional, Sequence

logger = logging.getLogger(__name__)

_MODEL_NAME = os.environ.get(
    "RAG_TEXT_EMBED_MODEL", "BAAI/bge-small-zh-v1.5")
_singleton = None


class TextEmbedder:
    def __init__(self, model_name: str = _MODEL_NAME,
                 device: Optional[str] = None):
        self._model_name = model_name
        self._device = device
        self._model = None
        self._dim = None

    def _lazy(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            import torch
        except ImportError as e:
            raise RuntimeError(f"sentence-transformers missing: {e}")
        dev = self._device
        if dev is None:
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("[text] loading %s on %s", self._model_name, dev)
        self._model = SentenceTransformer(self._model_name, device=dev)
        self._device = dev
        self._dim = self._model.get_sentence_embedding_dimension()

    @property
    def dim(self) -> int:
        self._lazy()
        return self._dim

    def encode(self, text: str) -> List[float]:
        return self.encode_batch([text or ""])[0]

    def encode_batch(self, texts: Sequence[str]) -> List[List[float]]:
        self._lazy()
        if not texts:
            return []
        clean = [t if t else " " for t in texts]
        vecs = self._model.encode(clean, normalize_embeddings=True,
                                   show_progress_bar=False)
        return vecs.tolist() if hasattr(vecs, "tolist") else [list(v) for v in vecs]


def get_text_embedder() -> TextEmbedder:
    global _singleton
    if _singleton is None:
        _singleton = TextEmbedder()
    return _singleton


__all__ = ["TextEmbedder", "get_text_embedder"]
