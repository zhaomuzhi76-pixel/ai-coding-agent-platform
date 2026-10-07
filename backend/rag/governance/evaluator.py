"""CLEAR 5 维评估编排器。

职责：
    - 调 L2 各维度计算
    - 聚合成 CLEARReport
    - 三级裁决：pass / warn / fail

不负责：
    - 各维度的实际算法（在 L2 各模块）
    - 与 RAG 检索耦合（用 hits 列表抽象）
"""
from __future__ import annotations

from typing import Any, Iterable, Optional, Tuple

from .citations import extract_citations
from .contracts import (
    CLEARReport,
    FaithfulnessReport,
    LatencyReport,
    RelevanceReport,
    RetrievalQuality,
)
from .faithfulness import score_faithfulness
from .latency import LatencyBudget
from .relevance import score_relevance
from .retrieval_quality import score_retrieval

# 裁决阈值（从 backend/config/rag_governance 读；env 可覆盖）
from backend.config.rag_governance import get_rag_config as _get_rag_cfg
_CFG = _get_rag_cfg()
FAITH_FAIL = _CFG.faith_fail
FAITH_PASS = _CFG.faith_pass
RELEVANCE_MIN = _CFG.relevance_min
COVERAGE_MIN = _CFG.coverage_min
DEFAULT_BUDGET_MS = _CFG.default_budget_ms


def evaluate(
    query: str,
    answer: str,
    hits: Iterable[Any],
    *,
    latency: Optional[LatencyReport] = None,
    min_relevant: float = 0.5,
    min_citation_score: float = 0.0,
) -> CLEARReport:
    """把 5 维计算结果聚合成 CLEARReport。"""
    # 一次性把 hits 固化（可迭代会耗尽）
    hits_list = list(hits)

    # ── C：引用抽取 ──
    cits = extract_citations(hits_list, min_score=min_citation_score)

    # ── E：证据忠实度（用引用的 snippet 作为 evidence）──
    evidence = [c.snippet for c in cits]
    faith = score_faithfulness(answer, evidence)

    # ── A：答案相关性 ──
    rel = score_relevance(query, answer)

    # ── R：检索质量 ──
    rq = score_retrieval(hits_list, min_relevant=min_relevant)

    # ── L：延迟（可传入，也可后续补）──
    lat = latency or LatencyReport()

    # ── 三级裁决 ──
    verdict, reason = _decide(faith, rel, rq)

    return CLEARReport(
        citations=cits,
        latency=lat,
        evidence=faith,
        answer=rel,
        retrieval=rq,
        verdict=verdict,
        reason=reason,
    )


async def evaluate_async(
    query: str,
    answer: str,
    hits: Iterable[Any],
    *,
    budget_ms: int = DEFAULT_BUDGET_MS,
    min_relevant: float = 0.5,
    min_citation_score: float = 0.0,
) -> CLEARReport:
    """带延迟预算的评估（自动计时 evaluate）。"""
    budget = LatencyBudget(budget_ms=budget_ms)
    budget.start()
    with budget.stage("evaluate"):
        report = evaluate(
            query, answer, hits,
            min_relevant=min_relevant,
            min_citation_score=min_citation_score,
        )
    report.latency = budget.report()
    return report


def _decide(
    faith: FaithfulnessReport,
    rel: RelevanceReport,
    rq: RetrievalQuality,
) -> Tuple[str, str]:
    """三级裁决：pass / warn / fail。

    优先级：
        1) faithfulness < 0.60 → fail（严重幻觉）
        2) faithfulness < 0.85 → warn（部分编造）
        3) relevance < 0.50  → warn（答非所问）
        4) coverage  < 0.40  → warn（检索质量低）
        5) 全部达标 → pass
    """
    if faith.total_claims == 0:
        return "warn", "答案为空或无法分句"
    if faith.score < FAITH_FAIL:
        return "fail", f"faithfulness={faith.score:.2f}<{FAITH_FAIL}（严重幻觉）"
    if faith.score < FAITH_PASS:
        return "warn", f"faithfulness={faith.score:.2f}<{FAITH_PASS}（部分编造）"
    if rel.score < RELEVANCE_MIN:
        return "warn", f"relevance={rel.score:.2f}<{RELEVANCE_MIN}（答非所问）"
    if rq.coverage < COVERAGE_MIN:
        return "warn", f"retrieval_coverage={rq.coverage:.2f}<{COVERAGE_MIN}（检索质量低）"
    return "pass", "全部维度达标"


__all__ = [
    "DEFAULT_BUDGET_MS",
    "FAITH_FAIL",
    "FAITH_PASS",
    "RELEVANCE_MIN",
    "COVERAGE_MIN",
    "evaluate",
    "evaluate_async",
]
