"""幻觉抑制守卫：依据 CLEARReport 决定 弃答 / 加提示 / 原样返回。

职责：
    - 评估 + 决策（三态：allow / annotate / abstain）
    - strict 模式：合规场景下任何不达标都升级为弃答

不负责：
    - 各维度实际计算（在 L2）
    - 与 LLM 交互（由上游调用）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .contracts import CLEARReport
from .evaluator import evaluate

# 工业级默认阈值（从 backend/config/rag_governance 读；env 可覆盖）
from backend.config.rag_governance import get_rag_config as _get_rag_cfg
_CFG = _get_rag_cfg()
DEFAULT_MIN_FAITH = _CFG.min_faith
DEFAULT_MIN_RELEVANCE = _CFG.min_relevance

ABSTAIN_TEXT = "抱歉，当前知识库中没有可靠证据支持这个问题的回答。"
ANNOTATE_PREFIX = "⚠️ 以下回答部分内容未能从知识库中核实："


@dataclass
class GuardDecision:
    """守卫决策结果。"""
    action: str        # "allow" | "annotate" | "abstain"
    answer: str        # 最终对外答案（可能被改写）
    reason: str
    report: CLEARReport


def guard_answer(
    query: str,
    answer: str,
    hits: Iterable[Any],
    *,
    min_faithfulness: float = DEFAULT_MIN_FAITH,
    min_relevance: float = DEFAULT_MIN_RELEVANCE,
    strict: bool = False,
) -> GuardDecision:
    """核心入口：评估 + 决策。

    strict=True 时任何 warn 都升级为 abstain（合规/医疗场景）。
    """
    report = evaluate(query, answer, hits)

    # 空答案 → 交上游处理
    if not answer.strip():
        return GuardDecision(
            action="allow", answer=answer,
            reason="空答案，无需守门", report=report,
        )

    f_score = report.evidence.score
    r_score = report.answer.score

    # ── 弃答：忠实度严重不足 ──
    if f_score < min_faithfulness:
        return GuardDecision(
            action="abstain",
            answer=ABSTAIN_TEXT,
            reason=f"faithfulness={f_score:.2f}<{min_faithfulness}（严重幻觉）",
            report=report,
        )

    # ── 相关性不达标 ──
    if r_score < min_relevance:
        if strict:
            return GuardDecision(
                action="abstain",
                answer=ABSTAIN_TEXT,
                reason=f"relevance={r_score:.2f}<{min_relevance}（strict 弃答）",
                report=report,
            )
        return GuardDecision(
            action="annotate",
            answer=f"{ANNOTATE_PREFIX}\n{answer}",
            reason=f"relevance={r_score:.2f}<{min_relevance}（答非所问）",
            report=report,
        )

    # ── pass：原样放行 ──
    if report.verdict == "pass":
        return GuardDecision(
            action="allow", answer=answer,
            reason="全部维度达标", report=report,
        )

    # ── warn：加提示 ──
    return GuardDecision(
        action="annotate",
        answer=f"{ANNOTATE_PREFIX}\n{answer}",
        reason=report.reason or "部分维度未达标",
        report=report,
    )


__all__ = [
    "ABSTAIN_TEXT", "ANNOTATE_PREFIX",
    "DEFAULT_MIN_FAITH", "DEFAULT_MIN_RELEVANCE",
    "GuardDecision", "guard_answer",
]
