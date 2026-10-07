"""工业级 RAG 治理契约（CLEAR 5 维）。

职责：
    - 定义 5 维评估报告结构
    - 定义 CLEARReport 聚合结果
    - 纯 dataclass，零业务依赖

不负责：
    - 实际计算（各维度独立模块）
    - 与 RAG 检索耦合（用适配层）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Citation:
    """单条可追溯引用（从 RagHit 抽取）。"""
    doc_id: str
    chunk_id: str
    snippet: str
    score: float
    source: str = ""
    line_no: int = 0
    role: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "snippet": self.snippet,
            "score": round(self.score, 4),
            "source": self.source,
            "line_no": self.line_no,
            "role": self.role,
        }


@dataclass
class LatencyReport:
    """延迟预算报告。"""
    stages: Dict[str, float] = field(default_factory=dict)
    total_ms: float = 0.0
    budget_ms: int = 3000
    over_budget: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stages": {k: round(v, 1) for k, v in self.stages.items()},
            "total_ms": round(self.total_ms, 1),
            "budget_ms": self.budget_ms,
            "over_budget": self.over_budget,
        }


@dataclass
class FaithfulnessReport:
    """证据忠实度报告（NLI-free 逐句判定）。"""
    score: float = 0.0
    total_claims: int = 0
    supported_claims: int = 0
    unsupported: List[str] = field(default_factory=list)

    @property
    def risk(self) -> str:
        if self.score >= 0.85:
            return "low"
        if self.score >= 0.6:
            return "medium"
        return "high"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "unsupported": self.unsupported[:5],
            "risk": self.risk,
        }


@dataclass
class RelevanceReport:
    """答案相关性报告。"""
    score: float = 0.0
    overlap_terms: List[str] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "overlap_terms": self.overlap_terms[:10],
            "missing_terms": self.missing_terms[:10],
        }


@dataclass
class RetrievalQuality:
    """检索质量指标。"""
    k: int = 0
    coverage: float = 0.0
    avg_score: float = 0.0
    top_score: float = 0.0
    mrr: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k": self.k,
            "coverage": round(self.coverage, 4),
            "avg_score": round(self.avg_score, 4),
            "top_score": round(self.top_score, 4),
            "mrr": round(self.mrr, 4) if self.mrr is not None else None,
        }


@dataclass
class CLEARReport:
    """CLEAR 五维工业级报告。"""
    citations: List[Citation] = field(default_factory=list)
    latency: LatencyReport = field(default_factory=LatencyReport)
    evidence: FaithfulnessReport = field(default_factory=FaithfulnessReport)
    answer: RelevanceReport = field(default_factory=RelevanceReport)
    retrieval: RetrievalQuality = field(default_factory=RetrievalQuality)
    verdict: str = "pass"
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "citation_count": len(self.citations),
            "citations": [c.to_dict() for c in self.citations[:5]],
            "latency": self.latency.to_dict(),
            "evidence": self.evidence.to_dict(),
            "answer": self.answer.to_dict(),
            "retrieval": self.retrieval.to_dict(),
        }


__all__ = [
    "Citation", "LatencyReport", "FaithfulnessReport",
    "RelevanceReport", "RetrievalQuality", "CLEARReport",
]
