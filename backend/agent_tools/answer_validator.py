"""答案校验与补全（工业级策略 B，v2）。
从 evidence hits 抽权威方剂 → 校验 LLM 答案的完整性 → 缺失时补全。
不重写抽取（formula_parser 管）、不调 LLM、不写 trace。

环境变量：
  RAG_CHAT_PATCH_ENABLED=1
  RAG_CHAT_AUTHORITATIVE_SOURCES=伤寒论,金匮要略,金匮,内经,神农本草经
"""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

from backend.agent_tools.formula_parser import (
    Formula, extract_formulas, split_herbs)

logger = logging.getLogger(__name__)

_ENABLED = os.environ.get("RAG_CHAT_PATCH_ENABLED", "1") == "1"
_PRIORITY = [s.strip() for s in os.environ.get(
    "RAG_CHAT_AUTHORITATIVE_SOURCES",
    "伤寒论,金匮要略,金匮,内经,神农本草经").split(",") if s.strip()]


def _source_priority(src: str) -> int:
    if not src:
        return 99
    for i, kw in enumerate(_PRIORITY):
        if kw in src:
            return i
    return 100


def _query_name(query: str) -> str:
    """从问题提方剂名：XX汤/丸/散/膏/丹。"""
    import re
    m = re.search(r'([\u4e00-\u9fff]{2,10}[汤丸散膏丹])', query or "")
    return m.group(1) if m else ""


def pick_authoritative(formulas: List[Formula],
                       query_name: str) -> Optional[Formula]:
    """选权威方剂：**方名精确匹配** + 经典方源优先。"""
    if not query_name:
        return None
    exact = [f for f in formulas if f.name == query_name and f.valid]
    if not exact:
        return None
    exact.sort(key=lambda f: (_source_priority(f.source),
                               -len(f.composition)))
    return exact[0]


@dataclass
class PatchResult:
    ok: bool
    answer: str
    missing: List[str] = field(default_factory=list)
    formula_name: str = ""
    source: str = ""
    reason: str = ""


def _missing(answer: str, formula: Formula) -> List[str]:
    a = answer or ""
    out = []
    for h in formula.composition:
        if h and h not in a:
            out.append(h)
    return out


def check_and_patch(query: str, answer: str,
                    hits: List[dict]) -> PatchResult:
    if not _ENABLED or not hits:
        return PatchResult(True, answer)
    # 抽所有方剂
    all_f: List[Formula] = []
    for h in hits:
        text = str(h.get("text") or "")
        if text:
            all_f.extend(extract_formulas(text))
    if not all_f:
        return PatchResult(True, answer)

    qname = _query_name(query)
    best = pick_authoritative(all_f, qname)
    if best is None:
        return PatchResult(True, answer)

    missing = _missing(answer, best)
    if not missing:
        return PatchResult(True, answer, formula_name=best.name,
                           source=best.source)

    herbs = "、".join(best.composition)
    src = f"（{best.source}）" if best.source else ""
    note = f"\n\n[补全] 依据原文{src}《{best.name}》完整组成：{herbs}"
    return PatchResult(False, (answer or "") + note, missing=missing,
                       formula_name=best.name, source=best.source,
                       reason=f"missing={missing[:3]}")


__all__ = ["Formula", "PatchResult", "extract_formulas", "split_herbs",
           "pick_authoritative", "check_and_patch", "_ENABLED", "_PRIORITY"]
