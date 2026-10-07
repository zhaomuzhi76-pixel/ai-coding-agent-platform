"""L2 RAG 治理领域层单测：CLEAR 5 维 + 幻觉抑制 + 插件钩子。"""
from __future__ import annotations

import asyncio
import time

from backend.rag.governance import (
    ABSTAIN_TEXT,
    ANNOTATE_PREFIX,
    LatencyBudget,
    RagGovernancePlugin,
    audit_citations_in_answer,
    citations_to_context,
    evaluate,
    evaluate_async,
    extract_citations,
    guard_answer,
    score_faithfulness,
    score_relevance,
    score_retrieval,
    should_abstain,
    split_claims,
)

from .framework import Suite, assert_eq, assert_true

suite = Suite("rag_governance")

_HITS = [
    {"chunk_id": "c1", "text": "Python 用缩进定义代码块", "score": 0.92,
     "source": "py.jsonl", "line_no": 3},
    {"chunk_id": "c2", "text": "Python 变量无需声明类型", "score": 0.78,
     "source": "py.jsonl", "line_no": 5},
    {"chunk_id": "c3", "text": "Go 使用花括号", "score": 0.21},
]

# ═══ C: Citations ═══

@suite.case
def citations_extract_basic():
    cits = extract_citations(_HITS)
    assert_eq(len(cits), 3)
    return f"{len(cits)} 条"

@suite.case
def citations_extract_min_score():
    cits = extract_citations(_HITS, min_score=0.5)
    assert_eq(len(cits), 2)
    return "跳过低分"

@suite.case
def citations_context_has_numbers():
    ctx = citations_to_context(extract_citations(_HITS[:2]))
    assert_true("[1]" in ctx and "[2]" in ctx)
    return "含 [1][2]"

@suite.case
def citations_audit_all_used():
    cits = extract_citations(_HITS[:2])
    a = audit_citations_in_answer("第一 [1] 第二 [2]", cits)
    assert_true(a["all_used"])
    return f"cited={a['cited_count']}"

# ═══ E: Faithfulness ═══

@suite.case
def faithfulness_real():
    r = score_faithfulness("Python 用缩进定义代码块[1]。",
                           ["Python 用缩进定义代码块"])
    assert_eq(r.score, 1.0)
    return f"score={r.score:.2f}"

@suite.case
def faithfulness_hallucination_detected():
    r = score_faithfulness("Python 用花括号定义代码块[1]。",
                           ["Python 用缩进定义代码块"])
    assert_true(r.score < 0.5, f"应低分, 实际 {r.score}")
    return f"score={r.score:.2f} risk={r.risk}"

@suite.case
def faithfulness_partial():
    r = score_faithfulness("Python 用缩进定义代码块[1]。Python 是 1991 年发布的。",
                           ["Python 用缩进定义代码块"])
    assert_true(0 < r.score < 1.0, f"应部分, 实际 {r.score}")
    return f"score={r.score:.2f}"

@suite.case
def faithfulness_empty_answer():
    r = score_faithfulness("", ["任意"])
    assert_eq(r.score, 1.0)
    assert_eq(r.total_claims, 0)
    return "空答案=1.0"

@suite.case
def faithfulness_should_abstain():
    r = score_faithfulness("Python 用花括号[1]。", ["Python 用缩进"])
    assert_true(should_abstain(r))
    return "建议弃答"

@suite.case
def faithfulness_split_claims():
    claims = split_claims("第一句[1]，第二句[2]。第三句[3]")
    assert_true(len(claims) >= 2, f"实际 {len(claims)}")
    return f"{len(claims)} 句"

# ═══ A: Relevance ═══

@suite.case
def relevance_match():
    r = score_relevance("Python 缩进", "Python 用缩进定义代码块")
    assert_true(r.score > 0.5)
    return f"score={r.score:.2f}"

@suite.case
def relevance_mismatch():
    r = score_relevance("量子计算 纠缠", "Python 用缩进")
    assert_true(r.score < 0.3)
    return f"score={r.score:.2f}"

# ═══ R: Retrieval ═══

@suite.case
def retrieval_quality_basic():
    r = score_retrieval(_HITS, min_relevant=0.5)
    assert_eq(r.k, 3)
    assert_eq(r.mrr, 1.0)
    return f"k={r.k} cov={r.coverage:.2f}"

# ═══ L: Latency ═══

@suite.case
def latency_under_budget():
    b = LatencyBudget(budget_ms=1000)
    b.start()
    with b.stage("work"):
        time.sleep(0.001)
    r = b.report()
    assert_true(not r.over_budget)
    return f"total={r.total_ms:.1f}ms"

@suite.case
def latency_over_budget():
    b = LatencyBudget(budget_ms=1)
    b.start()
    with b.stage("work"):
        time.sleep(0.01)
    r = b.report()
    assert_true(r.over_budget)
    return f"total={r.total_ms:.1f}ms"

# ═══ Evaluator 三级裁决 ═══

@suite.case
def evaluator_verdict_pass():
    r = evaluate("Python", "Python 用缩进定义代码块[1]。", _HITS)
    assert_eq(r.verdict, "pass")
    return r.reason

@suite.case
def evaluator_verdict_fail():
    r = evaluate("Python", "Python 用花括号定义代码块[1]。", _HITS)
    assert_eq(r.verdict, "fail")
    return r.reason

@suite.case
def evaluator_verdict_warn():
    r = evaluate("量子计算", "Python 用缩进定义代码块[1]。", _HITS)
    assert_eq(r.verdict, "warn")
    return r.reason

@suite.case
def evaluator_async_has_latency():
    r = asyncio.run(evaluate_async(
        "Python", "Python 用缩进定义代码块[1]。", _HITS, budget_ms=500))
    assert_true(r.latency.total_ms > 0)
    return f"latency={r.latency.total_ms:.1f}ms"

# ═══ Guard 决策 ═══

@suite.case
def guard_allow_real():
    d = guard_answer("Python", "Python 用缩进定义代码块[1]。", _HITS)
    assert_eq(d.action, "allow")
    return d.action

@suite.case
def guard_abstain_hallucination():
    d = guard_answer("Python", "Python 用花括号定义代码块[1]。", _HITS)
    assert_eq(d.action, "abstain")
    assert_eq(d.answer, ABSTAIN_TEXT)
    return f"action={d.action}"

@suite.case
def guard_strict_upgrades_warn():
    d = guard_answer("量子计算", "Python 用缩进定义代码块[1]。", _HITS, strict=True)
    assert_eq(d.action, "abstain")
    return "strict 升级为弃答"

@suite.case
def guard_annotate_non_strict():
    d = guard_answer("量子计算", "Python 用缩进定义代码块[1]。", _HITS, strict=False)
    assert_eq(d.action, "annotate")
    assert_true(d.answer.startswith(ANNOTATE_PREFIX))
    return f"action={d.action}"

# ═══ Plugin 三钩子 ═══

@suite.case
def plugin_append_context_hook():
    p = RagGovernancePlugin()
    out = p.append_context("原始", {"ok": True, "hits": _HITS, "count": 3})
    assert_true("[1]" in out)
    return f"{len(out)} 字符"

@suite.case
def plugin_three_hooks_chain():
    p = RagGovernancePlugin()
    assert_true(p.ready())
    d = p.guard("Python", "Python 用缩进定义代码块[1]。", _HITS)
    assert_eq(d.action, "allow")
    r = p.evaluate("Python", "Python 用缩进定义代码块[1]。", _HITS)
    assert_eq(r.verdict, "pass")
    return f"v={p.VERSION}"
