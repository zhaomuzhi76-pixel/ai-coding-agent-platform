"""图文双路检索编排（工业级）。

职责：
  - 一次 query 同时查文本库 + 图片库
  - 用不同模型干擅长的事（qwen3-emb 文本 / BGE 短文本找图）
  - 返回统一结构 {text, images, meta}

不做：
  - 不编码（embedder 管）
  - 不存储（vector_store 管）
  - 不调 LLM（L3 生成层管）

扩展点：
  - CLIP 路（图搜图）：预留 _search_by_image
  - VLM caption：预留 caption 增强
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from backend.rag.history_boost import (
    extract_classes_from_history, boost_by_history,
)

_TEXT_COLL = "agent_code_knowledge"
_IMG_COLL = "image_desc"
_IMG_KB = "image_desc"


@dataclass
class OrchestratedResult:
    query: str
    text: str = ""
    text_hits: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "text": self.text,
            "text_hits": self.text_hits,
            "images": self.images,
            "meta": self.meta,
        }



class RetrievalOrchestrator:
    def __init__(self):
        self._text_vs = None
        self._img_vs = None
        self._text_emb = None
        self._img_emb = None

    def _lazy_text(self):
        if self._text_vs is None:
            from backend.storage.vector_backend import get_vector_store
            from backend.storage.vector_config import VectorConfig
            from backend.api.rag.multimodal_runtime import get_multimodal_rag_runtime
            self._text_vs = get_vector_store(VectorConfig(collection_name=_TEXT_COLL))
            self._text_emb = get_multimodal_rag_runtime().embed_client
        return self._text_vs, self._text_emb

    def _lazy_img(self):
        if self._img_vs is None:
            from backend.storage.vector_backend import get_vector_store
            from backend.storage.vector_config import VectorConfig
            from backend.rag.multimodal.text_embedder import get_text_embedder
            self._img_vs = get_vector_store(VectorConfig(collection_name=_IMG_COLL))
            self._img_emb = get_text_embedder()
        return self._img_vs, self._img_emb

    # ---- 文本路 ----
    def _search_text(self, query: str, k: int) -> List[Dict[str, Any]]:
        """文本路检索（委托 retrieval_paths）。"""
        try:
            vs, emb_fn = self._lazy_text()
            from backend.rag.retrieval_paths import search_text as _st
            return _st(vs, emb_fn, query, k)
        except Exception as e:
            logger.warning("[orch] text search 失败: %r", e)
            return []

    # ---- 图片路 ----
    def _search_image(self, query: str, k: int) -> List[Dict[str, Any]]:
        """图片路检索（委托 retrieval_paths）。

        [MULTI] 若 query 含空格（改写后多药名）→ 拆分检索再合并。
        """
        try:
            vs, emb = self._lazy_img()
            from backend.rag.retrieval_paths import (
                search_image as _si, search_image_multi as _smi)
            if " " in query or "，" in query or "," in query:
                return _smi(vs, emb, query, k)
            return _si(vs, emb, query, k)
        except Exception as e:
            logger.warning("[orch] image search 失败: %r", e)
            return []

    # ---- 主编排 ----
    def search(self, query: str, *, k_text: int = 3,
               k_img: int = 8,
               history: Optional[list] = None) -> OrchestratedResult:
        """完整双路检索。

        Args:
            history: 可选。上轮 user/assistant 文本列表。用于：
              - 会话记忆加权（上轮出现过的类名 → 本轮提权）
        """
        q = (query or "").strip()
        if not q:
            return OrchestratedResult(query=q, meta={"error": "empty"})

        # [ALIAS_NORM] 别名归一（插件化 · 含双向词守卫）
        try:
            from backend.rag.plugins.alias_guard import apply_safe_alias
            q = apply_safe_alias(q, logger=logger)
        except Exception:
            pass

        # [MULTI_TURN] 提取 history 里的 class_name
        history_classes = extract_classes_from_history(history)
        if history_classes:
            logger.debug("[orch] history_classes=%s", history_classes)

        # [SKIP_IF_HAS_HERB] query 已含已知药材词 → 跳过 LLM 改写（防幻觉）
        q_img = q  # 默认用原 q
        try:
            from backend.agent_tools.query_rewriter import _load_herb_vocab
            _vocab = _load_herb_vocab() or set()
            _has_herb = any(n and n in q for n in _vocab)
        except Exception:
            _has_herb = False
        try:
            from backend.rag.llm_query_rewriter import get_rewriter
            _rw = get_rewriter()
            if (_rw.enabled() and not _has_herb
                    and _rw.needs_rewrite(q)):
                names = _rw.rewrite(q)
                if names:
                    q_img = " ".join(names)
                    logger.info("[orch] rewrite: %r → %r", q, q_img)
        except Exception as e:
            logger.debug("[orch] llm rewrite 失败: %r", e)

        text_hits = self._search_text(q, k_text)
        img_hits = self._search_image(q_img, k_img)

        # [MULTI_TURN] 图片：对上轮命中过的类提权
        if history_classes and img_hits:
            img_hits = boost_by_history(img_hits, history_classes, boost=1.5)

        # 主文本 = top1
        main_text = text_hits[0]["text"] if text_hits else ""

        return OrchestratedResult(
            query=q,
            text=main_text,
            text_hits=text_hits,
            images=img_hits,
            meta={
                "n_text": len(text_hits),
                "n_images": len(img_hits),
                "route": "dual",
                "models": ["qwen3-embedding:4b", "BGE-small-zh"],
                "history_classes": sorted(history_classes) if history_classes else [],
                "img_query": q_img,
            },
        )


_singleton: Optional[RetrievalOrchestrator] = None


def get_orchestrator() -> RetrievalOrchestrator:
    global _singleton
    if _singleton is None:
        _singleton = RetrievalOrchestrator()
    return _singleton


def _to_url(path: Optional[str]) -> str:
    """把 image_path 映射到 HTTP 可访问的 /data/images/... 路径。

    [FIX] 支持 3 种存储形式：
      A) data/CHM-100_download/CHM-100_extracted/dataset_split_train_test-100/train/1/11.jpg
         → /data/images/chm/train/1/11.jpg  (软链 data/images/chm → CHM-100 目录)
      B) data/images/tcm/page_001_00_xxx.png
         → /data/images/tcm/page_001_00_xxx.png
      C) /data/images/xxx 或 http(s)://xxx
         → 原样
    """
    if not path:
        return ""
    p = str(path).replace("\\", "/")

    # C) 绝对 / HTTP 直返
    if p.startswith("/") or p.startswith("http://") or p.startswith("https://"):
        return p

    # A) CHM-100：识别 dataset_split 前缀
    if "dataset_split_train_test-100/" in p:
        rel = p.split("dataset_split_train_test-100/", 1)[1]
        return f"/data/images/chm/{rel}"

    # B) data/images/ 前缀 → 加 /
    if p.startswith("data/images/"):
        return "/" + p

    # 兜底：在路径里找 /data/images/ 片段
    if "/data/images/" in p:
        tail = p.split("/data/images/", 1)[1]
        return f"/data/images/{tail}"

    # 真的不知道 → 原样（前端会 404，但至少有信息）
    return p



__all__ = ["RetrievalOrchestrator", "OrchestratedResult", "get_orchestrator"]
