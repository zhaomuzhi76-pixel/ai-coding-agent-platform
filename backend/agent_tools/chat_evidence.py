"""对话 RAG 证据层（工业级 v3）。
职责：hybrid_search + 质量过滤 + grounded 校验 + tier 排序，
      给 chat_loop 用（evidence-first）。
不构造 hint（chat_hint 管）、不校验答案（answer_validator 管）。
环境变量：
  RAG_CHAT_EVIDENCE_ENABLED=1
  RAG_CHAT_TOP_K=5
  RAG_CHAT_CONTEXT_MAX_CHARS=6000
  RAG_CHAT_REFUSE_THRESHOLD=0.75
  RAG_CHAT_MIN_RERANK=0.05
  RAG_CHAT_MIN_BM25=1.0
  RAG_CHAT_MIN_CN_RATIO=0.3
"""
from __future__ import annotations
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

_ENABLED = os.environ.get("RAG_CHAT_EVIDENCE_ENABLED", "1") == "1"
_TOP_K = int(os.environ.get("RAG_CHAT_TOP_K", "5"))
_CTX_MAX = int(os.environ.get("RAG_CHAT_CONTEXT_MAX_CHARS", "6000"))
_REFUSE_TH = float(os.environ.get("RAG_CHAT_REFUSE_THRESHOLD", "0.75"))
_MIN_RERANK = float(os.environ.get("RAG_CHAT_MIN_RERANK", "0.05"))
_MIN_BM25 = float(os.environ.get("RAG_CHAT_MIN_BM25", "1.0"))
_MIN_CN_RATIO = float(os.environ.get("RAG_CHAT_MIN_CN_RATIO", "0.3"))

_CN_RE = re.compile(r"[\u4e00-\u9fff]")
_VALID_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf"
                       r"a-zA-Z0-9\s，。；：！？、（）【】《》]")


@dataclass(frozen=True)
class Evidence:
    hits: Tuple[dict, ...]
    context_text: str
    confidence: float
    refused: bool
    reason: str
    error: str = ""
    images: Tuple[dict, ...] = ()   # [MM] 图文同返：图片列表
    images: Tuple[dict, ...] = ()   # [MM] 图文同返：图片列表

    @property
    def ok(self) -> bool:
        return not self.refused and bool(self.hits)


def enabled() -> bool:
    return _ENABLED


def _text_quality(text: str) -> float:
    if not text:
        return 0.0
    t = text.strip()
    valid = sum(1 for c in t if _VALID_RE.match(c))
    return valid / len(t)


def _has_rerank(h: dict) -> bool:
    rs = h.get("rerank_score")
    return rs is not None and float(rs) > 0.0


def _quality_pass(h: dict) -> bool:
    text = str(h.get("text") or "").strip()
    if len(text) < 20:
        return False
    cn = len(_CN_RE.findall(text))
    if cn / max(1, len(text)) < _MIN_CN_RATIO:
        return False
    if _text_quality(text) < 0.6:
        return False
    return True


def _score_filter(hits: List[dict]) -> Tuple[List[dict], str]:
    has_rr = any(_has_rerank(h) for h in hits)
    passed = []
    for h in hits:
        if has_rr:
            rs = float(h.get("rerank_score") or 0.0)
            if rs < _MIN_RERANK:
                continue
        else:
            bm = float(h.get("bm25_score") or 0.0)
            if bm < _MIN_BM25:
                continue
        passed.append(h)
    return passed, ("rerank" if has_rr else "bm25")


def collect(query: str, *, domains: Optional[List[str]] = None,
            top_k: Optional[int] = None,
            history_texts: Optional[List[str]] = None) -> Evidence:
    from backend.agent_tools.chat_hint import rewrite_query
    q = rewrite_query((query or "").strip(), history_texts)
    if not q:
        return Evidence((), "", 0.0, True, "empty_query")

    # [MM_FIRST] 优先走 multimodal orchestrator（文字 + 图片双路）
    try:
        from backend.rag.retrieval_orchestrator import get_orchestrator
        _orch = get_orchestrator()
        _r = _orch.search(q, k_text=max(int(top_k or _TOP_K), 3), k_img=8)
        _d = _r.to_dict()
        _txt = _d.get("text_hits") or []
        _imgs = _d.get("images") or []
        if _txt:
            _hits = []
            for _h in _txt:
                _hits.append({
                    "chunk_id": _h.get("chunk_id", ""),
                    "text": _h.get("text", ""),
                    "doc_title": _h.get("doc_title", ""),
                    "page": _h.get("page"),
                    "source": _h.get("source", ""),
                    "rerank_score": _h.get("rerank_score") or _h.get("score", 0.0),
                })
            _ctx = _fallback_ctx(_hits)
            return Evidence(
                hits=tuple(_hits), context_text=_ctx,
                confidence=0.85, refused=False, reason="",
                images=tuple(_imgs),
            )
    except Exception as _e:
        logger.warning("[chat_evidence] orchestrator 失败: %r", _e)

    k = int(top_k or _TOP_K)
    where = None
    if domains:
        dlist = [d for d in domains if d]
        if dlist:
            where = {"kb": {"$in": dlist}}

    # [TIERED_RANK] 全库搜 + 按古籍 tier 加权排序
    raw: List[dict] = []
    _meta: dict = {}
    try:
        from backend.agent_tools.tiered_retriever import tiered_rank
        raw, _meta = tiered_rank(q, k=max(k * 4, 30),
                                  where_extra=where,
                                  fetch_k=max(k * 10, 60))
    except Exception as e:
        logger.warning("[chat_evidence] tiered_rank 失败: %r", e)

    # 兜底：直接 hybrid
    if not raw:
        try:
            from backend.rag.hybrid.rag_integration import hybrid_search
            raw = hybrid_search(q, limit=max(k * 10, 60),
                                where=where, rerank=True) or []
        except Exception as e:
            logger.warning("[chat_evidence] hybrid 兜底失败: %r", e)
            return Evidence((), "", 0.0, True, "search_failed",
                            error=f"{type(e).__name__}: {e}")

    if not raw:
        return Evidence((), "", 0.0, True, "no_hits")

    scored, mode = _score_filter(raw)
    qualified = [h for h in scored if _quality_pass(h)]
    if not qualified:
        return Evidence(tuple(raw[:1]), "", 0.0, True,
                        f"quality_filter({len(scored)}/{len(raw)}_{mode})")
    qualified = qualified[:k]

    try:
        from backend.rag.generation.grounded import make_grounded_answer
        g = make_grounded_answer(q, qualified, answer="")
    except Exception as e:
        logger.warning("[chat_evidence] grounded 失败: %r", e)
        ctx = _fallback_ctx(qualified)
        return Evidence(tuple(qualified), ctx, 0.0, False, "", error=str(e))

    if g.refused:
        return Evidence(tuple(qualified), "", g.confidence, True, g.reason)
    ctx = (g.context_text or "").strip()
    if len(ctx) > _CTX_MAX:
        ctx = ctx[:_CTX_MAX] + "..."
    return Evidence(tuple(qualified), ctx, g.confidence, False, "")


# [INTENT] 问题意图 → evidence 字段优先级
_INTENT_RULES = [
    # (关键词, 意图, 优先字段)
    (("组成", "配方", "药材", "有哪些药"), "compose", ["组成", "配方"]),
    (("主治", "治什么", "治疗", "用于", "适应症"), "indication", ["主治", "功用", "疗效"]),
    (("功效", "作用", "效果", "能治"), "efficacy", ["功效", "功用", "作用"]),
    (("用法", "怎么用", "服用", "煎法"), "usage", ["用法", "用法用量"]),
    (("来源", "出处", "出自"), "source", ["来源", "方源"]),
    (("禁忌", "不能", "注意"), "caution", ["禁忌", "宜忌", "注意"]),
]


def _detect_intent(query: str) -> tuple:
    """识别用户意图。返回 (intent, prefer_fields)。"""
    q = (query or "").strip()
    if not q:
        return ("general", [])
    for kws, intent, fields in _INTENT_RULES:
        for kw in kws:
            if kw in q:
                return (intent, fields)
    return ("general", [])


def _filter_evidence_text(text: str, intent: str, prefer: list) -> str:
    """按意图从证据文本里挑相关字段（保留头部实体名 + 目标字段）。"""
    if intent == "general" or not text:
        return text
    lines = text.split("\n")
    out = []
    # 头部 2 行（实体名 + 出处）
    for l in lines[:2]:
        if l.strip():
            out.append(l)
    # 目标字段行（模糊匹配）
    for l in lines[2:]:
        s = l.strip()
        if not s:
            continue
        for f in prefer:
            if f in s:
                out.append(l)
                break
    # 目标字段一条都没命中 → 返回原文（兜底）
    if len(out) <= 2:
        return text
    return "\n".join(out)


def _fallback_ctx(hits: List[dict]) -> str:
    out = []
    for i, h in enumerate(hits, 1):
        text = str(h.get("text") or "")[:600]
        src = h.get("doc_title") or h.get("source") or ""
        page = h.get("page") or h.get("page_no") or 0
        head = f"[{i}]"
        if src:
            head += f" {src}"
        if page:
            head += f" p.{page}"
        out.append(f"{head}\n{text}")
    ctx = "\n\n".join(out)
    return ctx[:_CTX_MAX] + "..." if len(ctx) > _CTX_MAX else ctx


def build_hint(ev: Evidence) -> str:
    """转发到 chat_hint（保持向后兼容）。"""
    from backend.agent_tools.chat_hint import build_hint as _bh
    return _bh(ev)


__all__ = ["Evidence", "enabled", "collect", "build_hint",
           "rewrite_query",
           "_ENABLED", "_TOP_K", "_CTX_MAX", "_REFUSE_TH",
           "_MIN_RERANK", "_MIN_BM25", "_MIN_CN_RATIO"]


# 向后兼容：保留 rewrite_query 顶层导出
from backend.agent_tools.chat_hint import rewrite_query  # noqa: E402
