"""工业级 RAG 治理：CLEAR 5 维评估 + 幻觉抑制（插件式）。

设计：
    - 自下而上分层：contracts → L2 计算 → evaluator → guard → plugin
    - 不动现有 RAG 代码（用 wrapper 挂）
    - 单文件 ≤230 行

用法：
    from backend.rag.governance import wrap_rag_service
    service = wrap_rag_service(get_rag_service())
"""
from .contracts import (
    Citation,
    CLEARReport,
    FaithfulnessReport,
    LatencyReport,
    RelevanceReport,
    RetrievalQuality,
)

# ── L2 计算层 ──
from .citations import (
    audit_citations_in_answer,
    citations_to_context,
    extract_citations,
)
from .faithfulness import (
    score_faithfulness,
    should_abstain,
    split_claims,
)
from .latency import (
    DEFAULT_BUDGET_MS,
    LatencyBudget,
    stopwatch,
    summarize,
)
from .relevance import score_relevance
from .retrieval_quality import score_retrieval

# ── L3 编排层 ──
from .evaluator import (
    DEFAULT_BUDGET_MS as EVAL_DEFAULT_BUDGET_MS,
    FAITH_FAIL,
    FAITH_PASS,
    COVERAGE_MIN,
    RELEVANCE_MIN,
    evaluate,
    evaluate_async,
)
from .hallucination_guard import (
    ABSTAIN_TEXT, ANNOTATE_PREFIX, GuardDecision, guard_answer,
)
from .plugin import (
    RagGovernancePlugin, append_citation_context, build_citation_context,
)

from .bootstrap_hook import (
    install_rag_governance, uninstall_rag_governance,
)


__all__ = [
    # contracts
    "Citation", "CLEARReport", "FaithfulnessReport",
    "LatencyReport", "RelevanceReport", "RetrievalQuality",
    # citations
    "audit_citations_in_answer", "citations_to_context", "extract_citations",
    # faithfulness
    "score_faithfulness", "should_abstain", "split_claims",
    # latency
    "DEFAULT_BUDGET_MS", "LatencyBudget", "stopwatch", "summarize",
    # relevance / retrieval
    "score_relevance", "score_retrieval",
    # evaluator
    "EVAL_DEFAULT_BUDGET_MS", "FAITH_FAIL", "FAITH_PASS",
    "COVERAGE_MIN", "RELEVANCE_MIN",
    "evaluate", "evaluate_async",
    # hallucination_guard
    "ABSTAIN_TEXT", "ANNOTATE_PREFIX", "GuardDecision", "guard_answer",
    # plugin
    "RagGovernancePlugin", "build_citation_context", "append_citation_context",
    # bootstrap_hook
    "install_rag_governance", "uninstall_rag_governance",
]
