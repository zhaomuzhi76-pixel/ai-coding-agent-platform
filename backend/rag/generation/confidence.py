"""置信度计算 + 拒答判定"""
import math
import os as _os
from typing import List, Tuple

# [ENV] 拒答阈值可配（不写死）
REFUSE_THRESHOLD = float(_os.environ.get("RAG_CHAT_REFUSE_THRESHOLD", "0.75"))
MIN_HITS = int(_os.environ.get("RAG_CHAT_MIN_HITS", "1"))


def _norm(score: float) -> float:
    if score <= 0:
        return 0.0
    if score > 1.0:
        return 1.0 / (1.0 + math.exp(-score / 5.0))
    return max(0.0, min(1.0, score))


def calc_confidence(hits: List[dict], query: str = "") -> float:
    """top1 分（0.6）+ 命中数（0.2）+ 平均分（0.2）"""
    if not hits:
        return 0.0
    top = hits[0]
    top_score = _norm(float(top.get("rerank_score")
                            or top.get("score") or 0.0))
    hits_factor = min(1.0, len(hits) / 3.0)
    n = min(5, len(hits))
    avg = sum(_norm(float(h.get("rerank_score")
                          or h.get("score") or 0.0))
              for h in hits[:n]) / n
    return round(0.6 * top_score + 0.2 * hits_factor + 0.2 * avg, 4)


def should_refuse(confidence: float, hits: List[dict]) -> Tuple[bool, str]:
    if not hits:
        return True, "无检索命中"
    if len(hits) < MIN_HITS:
        return True, f"命中数不足 ({len(hits)}<{MIN_HITS})"
    if confidence < REFUSE_THRESHOLD:
        return True, f"置信度过低 ({confidence:.2f}<{REFUSE_THRESHOLD})"
    return False, ""


__all__ = ["REFUSE_THRESHOLD", "MIN_HITS",
           "calc_confidence", "should_refuse"]
