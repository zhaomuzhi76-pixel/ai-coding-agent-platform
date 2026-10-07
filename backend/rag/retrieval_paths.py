"""双路检索（文本 / 图片）——从 orchestrator 拆出的纯检索逻辑。

职责：
  - 文本路：qwen3-emb 或 BGE 编码 → text collection
  - 图片路：BGE 编码 → image_desc collection（含 FILTER_V2）
  - 拒答短路：无药材词的 query → 直接空

不做：
  - 不 RRF、不 boost（orchestrator 管）
  - 不生成、不改写（各自模块管）
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_IMG_COLL = "image_desc"
_TEXT_COLL = "agent_code_knowledge"

# FILTER_V2 阈值
_MIN_SCORE_LONG = 0.30
_STRICT_LEN = 6


def _to_url(path: Optional[str]) -> str:
    """把 image_path 映射到 HTTP 可达的 /data/images/...（含 URL 编码）。

    [QUOTE] 路径段用 quote(safe="/") 编码：空格/括号/中文安全。
    """
    if not path:
        return ""
    from urllib.parse import quote as _q

    p = str(path).replace("\\", "/")
    if p.startswith("/") or p.startswith("http://") or p.startswith("https://"):
        return p

    def _enc(rel: str) -> str:
        return _q(rel, safe="/")

    if "dataset_split_train_test-100/" in p:
        rel = p.split("dataset_split_train_test-100/", 1)[1]
        return f"/data/images/chm/{_enc(rel)}"
    if "tcmp-300/" in p:
        rel = p.split("tcmp-300/", 1)[1]
        return f"/data/images/tcmp300/{_enc(rel)}"
    if p.startswith("data/images/"):
        return "/" + _enc(p[len("data/images/"):])
    if "/data/images/" in p:
        tail = p.split("/data/images/", 1)[1]
        return f"/data/images/{_enc(tail)}"
    return p


def _has_herb_word(query: str) -> bool:
    """query 里是否含已知药材词。用于 negative 短路。"""
    try:
        from backend.agent_tools.query_rewriter import _load_herb_vocab
        vocab = _load_herb_vocab() or set()
    except Exception:
        return True  # 无法判断时不短路（保持兼容）
    q = str(query or "")
    for n in vocab:
        if n and n in q:
            return True
    return False


def _img_query_once(vs_img, embedder, q: str, k: int,
                    strict: bool) -> List[Dict[str, Any]]:
    """单次检索 + 过滤。"""
    qv = embedder.encode(q)
    r = vs_img.query([qv], n_results=max(k * 3, 15))
    ids = (r.get("ids") or [[]])[0]
    metas = (r.get("metadatas") or [[]])[0]
    dists = (r.get("distances") or [[]])[0]
    hits = []
    for i, cid in enumerate(ids):
        m = metas[i] if i < len(metas) else {}
        cls = m.get("class_name", "")
        sc = 1.0 - (dists[i] if i < len(dists) else 1.0)
        if cls:
            if strict:
                if q not in cls and cls not in q:
                    continue
            else:
                if sc < _MIN_SCORE_LONG:
                    continue
        hits.append({
            "id": cid,
            "class_name": cls,
            "latin": m.get("latin", ""),
            "url": _to_url(m.get("image_path")),
            "image_path": m.get("image_path"),
            "score": sc,
            "source": m.get("source", ""),
        })
        if len(hits) >= k:
            break
    return hits


def _exact_lookup(vs_img, query: str, k: int) -> List[Dict[str, Any]]:
    """[EXACT] where=class_name 精确查（不依赖向量，兜底罕见字）。

    用途：BGE 对生僻字（如"葶苈"）编码后 top-15 排不进 → 用 Chroma
    where 过滤直接命中。仅当 strict 主路径空时触发。
    """
    try:
        q = str(query or "").strip()
        if not q or len(q) > 8:
            return []
        coll = getattr(vs_img, "collection", None) or vs_img
        got = coll.get(where={"class_name": q}, limit=max(k, 5),
                       include=["metadatas"])
        ids = got.get("ids") or []
        metas = got.get("metadatas") or []
        hits = []
        for i, cid in enumerate(ids):
            m = metas[i] if i < len(metas) else {}
            cls = m.get("class_name", "")
            if cls != q:
                continue
            hits.append({
                "id": cid,
                "class_name": cls,
                "latin": m.get("latin", ""),
                "url": _to_url(m.get("image_path")),
                "image_path": m.get("image_path"),
                "score": 0.5,   # 精确兜底给中间分
                "source": m.get("source", ""),
                "_exact": True,
            })
            if len(hits) >= k:
                break
        return hits
    except Exception as e:
        logger.debug("[paths] exact_lookup 失败: %r", e)
        return []


def search_image(vs_img, embedder, query: str, k: int) -> List[Dict[str, Any]]:
    """图片路检索（含 FILTER_V2 + 拒答短路 + 模板双路）。"""
    try:
        q = str(query or "").strip()
        if not q:
            return []
        # [NEG_STRICT] 长 query 且无任何药材词 → 空（拒答）
        # 例外：query 已被 LLM 改写成药名列表（含空格），交给 multi 处理
        _has_space = " " in q or "，" in q or "," in q
        if len(q) > _STRICT_LEN and not _has_herb_word(q) and not _has_space:
            return []
        # 无空格 且 无药材词 → 空（覆盖"Python 异步"等）
        if not _has_space and not _has_herb_word(q):
            return []

        qv = embedder.encode(q)
        r = vs_img.query([qv], n_results=max(k * 3, 15))
        ids = (r.get("ids") or [[]])[0]
        metas = (r.get("metadatas") or [[]])[0]
        dists = (r.get("distances") or [[]])[0]

        strict = len(q) <= _STRICT_LEN and " " not in q

        # 路 1：原 query 严格检索
        hits = _img_query_once(vs_img, embedder, q, k, strict)
        if hits:
            return hits

        # [EXACT_FALLBACK] 路 2：短 query 且 strict → where 精确查
        if strict:
            hits_e = _exact_lookup(vs_img, q, k)
            if hits_e:
                logger.info("[paths] exact fallback: %r → %d hits", q, len(hits_e))
                return hits_e

        # 路 3：短 query 加模板（应对 BGE 编码偏差）
        if strict:
            for tmpl in (f"{q} 中药材", f"{q} 植物", f"{q} 图片"):
                hits2 = _img_query_once(vs_img, embedder, tmpl, k, strict=False)
                hits2 = [h for h in hits2 if q in (h.get("class_name") or "")]
                if hits2:
                    logger.info("[paths] template fallback: %r → %d hits", q, len(hits2))
                    return hits2
        return []
    except Exception as e:
        logger.warning("[paths] image search 失败: %r", e)
        return []


def search_text(vs_text, embed_fn, query: str, k: int) -> List[Dict[str, Any]]:
    """文本路检索。"""
    try:
        q = str(query or "").strip()
        if not q:
            return []
        qv = embed_fn([q])[0] if callable(embed_fn) else embed_fn.encode(q)
        r = vs_text.query([qv], n_results=k)
        ids = (r.get("ids") or [[]])[0]
        metas = (r.get("metadatas") or [[]])[0]
        docs = (r.get("documents") or [[]])[0]
        dists = (r.get("distances") or [[]])[0]
        hits = []
        for i, cid in enumerate(ids):
            m = metas[i] if i < len(metas) else {}
            hits.append({
                "chunk_id": cid,
                "text": (docs[i] if i < len(docs) else "")[:500],
                "score": 1.0 - (dists[i] if i < len(dists) else 1.0),
                "doc_title": m.get("user_title") or m.get("doc_title", ""),
                "page": m.get("page_no"),
                "source": m.get("source_path") or m.get("doc_path", ""),
            })
        return hits
    except Exception as e:
        logger.warning("[paths] text search 失败: %r", e)
        return []




def search_image_multi(vs_img, embedder, query: str, k: int,
                        max_terms: int = 6) -> List[Dict[str, Any]]:
    """多药名分别检索 + 合并（避免单 query 向量稀释）。

    用法：
      query = "桑叶 菊花 杏仁"  →  拆 3 个 → 每个 top-1 → 合并去重
      与 search_image 的区别：那个是单 query 检索。
    """
    try:
        q = str(query or "").strip()
        if not q:
            return []
        # [NEG] 无药材词 → 空
        if len(q) > _STRICT_LEN and not _has_herb_word(q):
            # 但短词的也检查下
            pass

        # 拆分：空格/中文逗号/顿号
        import re as _re
        terms = [t for t in _re.split(r"[\s，,、]+", q) if t]
        # 单 term：走原逻辑（严格过滤更安全）
        if len(terms) <= 1:
            return search_image(vs_img, embedder, q, k)

        # 多 term：每个分别检索 top-N，合并
        # [EXACT_ONLY] 拆分后每个 term 只接受 term == class_name 精确命中
        # 避免 "茯苓" 命中 "土茯苓" 之类的 substring 误召回
        terms = terms[:max_terms]
        merged = {}
        for term in terms:
            term_s = term.strip()
            if not term_s:
                continue
            try:
                # 直接走 vs.query（不走 search_image 的 substring 过滤）
                qv = embedder.encode(term_s)
                r = vs_img.query([qv], n_results=8)
                ids = (r.get("ids") or [[]])[0]
                metas = (r.get("metadatas") or [[]])[0]
                dists = (r.get("distances") or [[]])[0]
                for i, cid in enumerate(ids):
                    m = metas[i] if i < len(metas) else {}
                    cls = m.get("class_name", "")
                    # [EXACT] 严格相等
                    if cls != term_s:
                        continue
                    sc = 1.0 - (dists[i] if i < len(dists) else 1.0)
                    h = {
                        "id": cid,
                        "class_name": cls,
                        "latin": m.get("latin", ""),
                        "url": _to_url(m.get("image_path")),
                        "image_path": m.get("image_path"),
                        "score": sc,
                        "source": m.get("source", ""),
                        "_from_term": term_s,
                    }
                    key = cid
                    if key not in merged or sc > float(merged[key].get("score") or 0):
                        merged[key] = h
            except Exception:
                continue

        out = sorted(merged.values(),
                     key=lambda x: -float(x.get("score") or 0.0))
        return out[:k]
    except Exception as e:
        logger.warning("[paths] multi search 失败: %r", e)
        return []

__all__ = ["search_image", "search_image_multi", "search_text", "_to_url"]
