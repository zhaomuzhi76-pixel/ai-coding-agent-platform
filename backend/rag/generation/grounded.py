"""Grounded 生成器：检索结果 → 强约束上下文 → GroundedAnswer"""
from typing import List

from .confidence import calc_confidence, should_refuse
from .contracts import Citation, GroundedAnswer
from .prompt import REFUSAL_TEXT, build_prompt, format_context


def _make_citations(hits: List[dict], limit: int = 10) -> tuple:
    out = []
    for i, h in enumerate(hits[:limit], 1):
        text = (h.get("text") or "").strip()
        out.append(Citation(
            idx=i,
            chunk_id=str(h.get("chunk_id") or h.get("id") or ""),
            source=str(h.get("source") or h.get("doc_title") or ""),
            page=int(h.get("page") or h.get("page_no") or 0),
            score=float(h.get("rerank_score") or h.get("score") or 0.0),
            excerpt=text[:200],
        ))
    return tuple(out)


def build_grounded_context(hits: List[dict]) -> str:
    return format_context(hits)


def make_grounded_answer(query: str, hits: List[dict],
                         answer: str = "") -> GroundedAnswer:
    conf = calc_confidence(hits, query)
    refused, reason = should_refuse(conf, hits)
    cits = _make_citations(hits)
    ctx = build_grounded_context(hits) if not refused else ""

    if refused:
        return GroundedAnswer(
            query=query, answer=REFUSAL_TEXT, citations=cits,
            confidence=conf, refused=True, reason=reason, context_text="",
        )
    return GroundedAnswer(
        query=query, answer=answer or "", citations=cits,
        confidence=conf, refused=False, reason="", context_text=ctx,
    )


def format_answer_with_citations(ans: GroundedAnswer) -> str:
    if ans.refused:
        return ans.answer
    parts = [ans.answer, ""]
    if ans.citations:
        parts.append("**来源：**")
        for c in ans.citations:
            line = f"  [{c.idx}] {c.source}"
            if c.page:
                line += f" p.{c.page}"
            parts.append(line)
    return "\n".join(parts)


__all__ = ["build_grounded_context", "make_grounded_answer",
           "format_answer_with_citations", "build_prompt"]
