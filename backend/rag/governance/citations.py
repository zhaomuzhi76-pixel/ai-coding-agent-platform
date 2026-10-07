"""引用抽取 + 溯源。工业级：每条回答都能追溯到原始 chunk。"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .contracts import Citation


def _get(obj: Any, *keys: str, default: Any = "") -> Any:
    for k in keys:
        if isinstance(obj, dict):
            v = obj.get(k)
        else:
            v = getattr(obj, k, None)
        if v is not None and v != "":
            return v
    return default


def _trim(text: str, n: int) -> str:
    t = " ".join(str(text).split())
    return t if len(t) <= n else t[: n - 1] + "…"


def extract_citations(
    hits: Iterable[Any],
    *,
    max_snippet: int = 200,
    min_score: float = 0.0,
) -> List[Citation]:
    """从 hits（RagHit 或 dict）抽取引用；跳过低分与空内容。"""
    out: List[Citation] = []
    for idx, h in enumerate(hits):
        try:
            score_f = float(_get(h, "score", "similarity", default=0.0))
        except (TypeError, ValueError):
            score_f = 0.0
        if score_f < min_score:
            continue
        doc_id = str(_get(h, "source", "source_path", "doc_id", default=f"doc-{idx}"))
        chunk_id = str(_get(h, "chunk_id", "id", default=f"c-{idx}"))
        snippet = _trim(
            _get(h, "text", "content", "snippet", default=""),
            max_snippet,
        )
        if not snippet:
            continue
        out.append(Citation(
            doc_id=doc_id,
            chunk_id=chunk_id,
            snippet=snippet,
            score=score_f,
            source=str(_get(h, "source", "file", "path", default="")),
            line_no=int(_get(h, "line_no", default=0)),
            role=str(_get(h, "role", default="")),
        ))
    return out


def citations_to_context(
    citations: List[Citation], *, header: bool = True,
) -> str:
    """拼成 LLM 可读的带 [N] 标号上下文。"""
    lines: List[str] = []
    if header:
        lines.append("【参考资料】每条前面 [N] 为引用编号，回答时必须标注引用编号。")
    for i, c in enumerate(citations, 1):
        src = f" ({c.source}:{c.line_no})" if c.source else ""
        lines.append(f"[{i}]{src} {c.snippet}")
    return "\n".join(lines)


def audit_citations_in_answer(
    answer: str, citations: List[Citation],
) -> Dict[str, Any]:
    """检查答案里是否用 [N] 引用了每条 citation。"""
    cited, unused = [], []
    for i, _ in enumerate(citations, 1):
        if f"[{i}]" in answer:
            cited.append(i)
        else:
            unused.append(i)
    return {
        "cited_count": len(cited),
        "unused_count": len(unused),
        "cited_indices": cited,
        "unused_indices": unused,
        "all_used": len(unused) == 0 and len(cited) > 0,
    }


__all__ = ["extract_citations", "citations_to_context", "audit_citations_in_answer"]
