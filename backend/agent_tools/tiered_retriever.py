"""两阶段检索（工业级 v3）。
策略：**先只在古籍里搜，够用就停**；不够才降级到全库。

阶段 1：只搜 tier_1（伤寒论/金匮/黄帝内经/神农/难经）
  有效命中 >= RAG_TIER_STAGE1_MIN → 直接用，杜绝大辞典污染
阶段 2：tier_1 + tier_2（官修大典）
  有效命中 >= RAG_TIER_STAGE2_MIN → 用
阶段 3：全库（大辞典等）
  兜底

不调 LLM、不写 trace。
环境变量：
  RAG_TIERED_ENABLED=1        总开关
  RAG_TIER_STAGE1_MIN=2       阶段 1 最少有效条数
  RAG_TIER_STAGE2_MIN=3       阶段 2 最少有效条数
  RAG_TIER_BOOST_T1=1.5       tier_1 排序加权
  RAG_TIER_BOOST_T2=1.2
  RAG_TIER_BOOST_T3=1.05
"""
from __future__ import annotations
from backend.agent_tools.text_normalizer import normalize_hits as _nh
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_ENABLED = os.environ.get("RAG_TIERED_ENABLED", "1") == "1"
_STAGE1_MIN = int(os.environ.get("RAG_TIER_STAGE1_MIN", "2"))
_STAGE2_MIN = int(os.environ.get("RAG_TIER_STAGE2_MIN", "3"))
_BOOST = {
    1: float(os.environ.get("RAG_TIER_BOOST_T1", "1.5")),
    2: float(os.environ.get("RAG_TIER_BOOST_T2", "1.2")),
    3: float(os.environ.get("RAG_TIER_BOOST_T3", "1.05")),
}

_CN_RE = re.compile(r'[\u4e00-\u9fff]')


def _tier_names(tier: int) -> List[str]:
    """从 yaml 拿该 tier 的所有名称。"""
    try:
        from backend.config.tcm_classics import list_all
        return [n for t, n in list_all() if t == tier]
    except Exception:
        return []


def _title_tier(title: str) -> int:
    try:
        from backend.config.tcm_classics import priority_of
        return priority_of(title)
    except Exception:
        return 99


_FORMULA_RE = re.compile(r'[\u4e00-\u9fff]{2,6}[汤丸散膏丹饮]')


def _extract_entities(query: str) -> List[str]:
    """从 query 提"方剂名"（XX汤/丸/散/膏/丹/饮）。"""
    if not query:
        return []
    # 优先"XX汤"（长优先，防拆短）
    found = _FORMULA_RE.findall(query)
    # 去重 + 去短
    seen = []
    for f in sorted(set(found), key=lambda x: -len(x)):
        if not any(f in s for s in seen):
            seen.append(f)
    return seen


def _relevance_pass(h: dict, entities: List[str]) -> bool:
    """命中是否真相关（不是强拉候选）。
    规则：
      - query 有方剂名 → hit.text 必须含方剂名（精确匹配）
      - query 无方剂名 → 用 bm25_score 门槛
    """
    text = str(h.get("text") or "")
    if not text:
        return False
    if entities:
        return any(e in text for e in entities)
    bm = float(h.get("bm25_score") or 0.0)
    return bm >= 1.0


def _filter_relevant(hits: List[dict], query: str) -> List[dict]:
    """按相关性过滤。"""
    entities = _extract_entities(query)
    return [h for h in hits if _relevance_pass(h, entities)]


def _valid_count(hits: List[dict], query: str = "") -> int:
    """过滤后有效命中数。"""
    n = 0
    entities = _extract_entities(query)
    for h in hits:
        t = str(h.get("text") or "").strip()
        if len(t) < 20:
            continue
        if len(_CN_RE.findall(t)) / max(1, len(t)) < 0.3:
            continue
        if not _relevance_pass(h, entities):
            continue
        n += 1
    return n


def _dedup(hits: List[dict]) -> List[dict]:
    seen, out = set(), []
    for h in hits:
        cid = h.get("chunk_id") or h.get("id")
        if cid and cid in seen:
            continue
        if cid:
            seen.add(cid)
        out.append(h)
    return out


def _score_of(h: dict) -> float:
    try:
        return float(h.get("rerank_score") or h.get("score") or 0.0)
    except Exception:
        return 0.0


def _boosted(h: dict) -> float:
    m = dict(h.get("metadata") or {})
    t = _title_tier(m.get("user_title") or m.get("doc_title") or "")
    return _score_of(h) * _BOOST.get(t, 1.0)


def _search_by_titles(query: str, titles: List[str], *,
                      where_extra: Optional[dict], per_book_k: int
                      ) -> List[dict]:
    """循环按 user_title 查（Lite 不支持 $in）。"""
    try:
        from backend.rag.hybrid.rag_integration import hybrid_search
    except Exception:
        return []
    out: List[dict] = []
    for t in titles:
        w = {"user_title": t}
        if where_extra:
            w.update(where_extra)
        try:
            hits = hybrid_search(query, limit=per_book_k, where=w,
                                 rerank=True) or []
            _nh(hits)  # [NORM] Kangxi→简体（text_normalizer 单点职责）
            out.extend(hits)
        except Exception as e:
            logger.debug("[tiered] title=%s 失败: %r", t, e)
    return out


def tiered_rank(query: str, *, k: int = 8,
                where_extra: Optional[dict] = None,
                fetch_k: Optional[int] = None
                ) -> Tuple[List[dict], Dict[str, Any]]:
    meta: Dict[str, Any] = {"stage": 0, "stage_counts": {}}
    if not _ENABLED or not query:
        return [], meta

    # [RELEVANCE_GATE] 无方剂名/术语 → 古籍阶段无意义，直接全库
    entities = _extract_entities(query)
    meta["entities"] = entities
    if not entities:
        meta["stage"] = 3
        try:
            from backend.rag.hybrid.rag_integration import hybrid_search
            _fetch = fetch_k or max(k * 10, 60)
            raw = hybrid_search(query, limit=_fetch,
                                where=where_extra, rerank=True) or []
            _nh(raw)  # [NORM] Kangxi→简体
            raw.sort(key=_boosted, reverse=True)
            meta["stage_counts"][3] = {"hits": len(raw)}
            return raw[:k], meta
        except Exception as e:
            logger.warning("[tiered] stage3 失败: %r", e)
            return [], meta

    per_book = max(k, 4)

    # ── 阶段 1：tier_1 古籍 ──
    tier1 = _tier_names(1)
    s1_raw = _search_by_titles(query, tier1,
                                where_extra=where_extra, per_book_k=per_book)
    s1 = _dedup(_filter_relevant(s1_raw, query))
    s1_valid = _valid_count(s1, query)
    meta["stage_counts"][1] = {"titles": tier1, "raw": len(s1_raw),
                                "filtered": len(s1), "valid": s1_valid}
    if s1_valid >= _STAGE1_MIN:
        s1.sort(key=_boosted, reverse=True)
        meta["stage"] = 1
        return s1[:k], meta

    # ── 阶段 2：tier_1 + tier_2 ──
    tier2 = _tier_names(2)
    s2_raw = _search_by_titles(query, tier1 + tier2,
                                where_extra=where_extra, per_book_k=per_book)
    s2 = _dedup(_filter_relevant(s2_raw, query))
    s2_valid = _valid_count(s2, query)
    meta["stage_counts"][2] = {"titles": tier1 + tier2,
                                "raw": len(s2_raw),
                                "filtered": len(s2), "valid": s2_valid}
    if s2_valid >= _STAGE2_MIN:
        s2.sort(key=_boosted, reverse=True)
        meta["stage"] = 2
        return s2[:k], meta

    # ── 阶段 3：全库 ──
    try:
        from backend.rag.hybrid.rag_integration import hybrid_search
        _fetch = fetch_k or max(k * 10, 60)
        raw = hybrid_search(query, limit=_fetch,
                            where=where_extra, rerank=True) or []
        raw.sort(key=_boosted, reverse=True)
        meta["stage"] = 3
        meta["stage_counts"][3] = {"hits": len(raw)}
        return raw[:k], meta
    except Exception as e:
        logger.warning("[tiered] stage3 失败: %r", e)
        return [], meta


__all__ = ["tiered_rank", "_ENABLED", "_STAGE1_MIN", "_STAGE2_MIN", "_BOOST"]
