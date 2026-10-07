"""证据忠实度：NLI-free 逐句判定。

工业级判定（AND 双判 + 子串逃生门）：
    1) 子串直命中：claim 清洗后是 evidence 的子串（或反之）→ 直接 supported
    2) 否则必须同时满足：
        - token 覆盖率 ≥ 0.85（防止中文单字虚高）
        - 3-gram Jaccard ≥ 0.60（防止通用字蒙混）

与「or」判定的区别：
    幻觉场景 "缩进→花括号" 时：
        token 覆盖 0.636 < 0.85 → 直接挡
        （旧 or 判定：0.636 ≥ 0.55 → 漏检）
"""
from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Set

from .contracts import FaithfulnessReport

_SENT_SPLIT = re.compile(r"(?<=[。！？；\.!?;，,])\s*")
_WORD = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")
_REF_MARK = re.compile(r"\[\d+\]")
_PUNCT = re.compile(
    r"[\s\u3000，。！？；：、（）【】「」『』《》·"
    r",.!?;:()\[\]{}<>\"'`~@#$%^&*+=|\\/_-]+"
)


def split_claims(text: str, *, min_chars: int = 6) -> List[str]:
    """切句；过滤过短 / 无内容。"""
    if not text:
        return []
    out: List[str] = []
    for raw in _SENT_SPLIT.split(text):
        s = raw.strip()
        if len(s) < min_chars:
            continue
        if not _WORD.search(s):
            continue
        out.append(s)
    return out


def _tokens(text: str) -> Set[str]:
    """中英文混切：中文单字 + 英文/数字整词。"""
    return {m.group(0).lower() for m in _WORD.finditer(text or "")}


def _evidence_pool(evidence: Iterable[str]) -> Set[str]:
    pool: Set[str] = set()
    for e in evidence:
        pool |= _tokens(e)
    return pool


def _ngrams(text: str, n: int = 3) -> Set[str]:
    """字符级 n-gram（忽略空白）。"""
    t = re.sub(r"\s+", "", text or "")
    if len(t) < n:
        return {t} if t else set()
    return {t[i : i + n] for i in range(len(t) - n + 1)}


def _coverage(claim: str, pool: Set[str]) -> float:
    """claim 的 token 在 evidence 池里的覆盖率。"""
    ct = _tokens(claim)
    if not ct:
        return 0.0
    return len(ct & pool) / len(ct)


def _ngram_jaccard(claim: str, evidence_texts: Sequence[str]) -> float:
    """claim 与任一 evidence 的 3-gram Jaccard 最大值。"""
    cg = _ngrams(claim, 3)
    if not cg:
        return 0.0
    best = 0.0
    for e in evidence_texts:
        eg = _ngrams(e, 3)
        if not eg:
            continue
        j = len(cg & eg) / len(cg | eg)
        if j > best:
            best = j
    return best


def _strip_noise(text: str) -> str:
    """去引用标号 + 空白 + 标点（用于子串直命中判定）。"""
    t = _REF_MARK.sub("", text or "")
    t = _PUNCT.sub("", t)
    return t


def _direct_substring(claim: str, evidence_texts: Sequence[str]) -> bool:
    """claim 清洗后是 evidence 的子串（或反之）。"""
    c = _strip_noise(claim)
    if not c:
        return False
    for e in evidence_texts:
        ec = _strip_noise(e)
        if not ec:
            continue
        if c in ec or ec in c:
            return True
    return False


def score_faithfulness(
    answer: str,
    evidence: Iterable[str],
    *,
    token_threshold: float = 0.85,
    ngram_threshold: float = 0.60,
) -> FaithfulnessReport:
    """逐句 AND 双判 + 子串逃生门。"""
    ev_list: List[str] = [e for e in evidence if e]
    pool = _evidence_pool(ev_list)
    claims = split_claims(answer)
    if not claims:
        return FaithfulnessReport(score=1.0, total_claims=0, supported_claims=0)
    supported, unsupported = 0, []
    for c in claims:
        if _direct_substring(c, ev_list):
            supported += 1
            continue
        cov = _coverage(c, pool)
        jac = _ngram_jaccard(c, ev_list)
        if cov >= token_threshold and jac >= ngram_threshold:
            supported += 1
        else:
            unsupported.append(c.strip())
    score = supported / len(claims)
    return FaithfulnessReport(
        score=score,
        total_claims=len(claims),
        supported_claims=supported,
        unsupported=unsupported,
    )


def should_abstain(report: FaithfulnessReport, *, min_score: float = 0.6) -> bool:
    """低忠实度 → 建议弃答（避免幻觉）。"""
    return report.total_claims > 0 and report.score < min_score


__all__ = ["split_claims", "score_faithfulness", "should_abstain"]
