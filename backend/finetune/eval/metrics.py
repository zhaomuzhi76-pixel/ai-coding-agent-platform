"""Evaluation metrics for finetune."""
from __future__ import annotations

import math
from typing import List


def exact_match(pred: str, gold: str) -> bool:
    return pred.strip() == gold.strip()


def contains_match(pred: str, gold: str) -> bool:
    g = gold.strip()
    if not g:
        return False
    return g in pred


def token_f1(pred: str, gold: str) -> float:
    p_tokens = pred.strip().split()
    g_tokens = gold.strip().split()
    if not p_tokens or not g_tokens:
        return 0.0
    common = set(p_tokens) & set(g_tokens)
    if not common:
        return 0.0
    precision = len(common) / len(p_tokens)
    recall = len(common) / len(g_tokens)
    return 2 * precision * recall / (precision + recall)


def perplexity_stub(losses: List[float]) -> float:
    if not losses:
        return 0.0
    mean = sum(losses) / len(losses)
    return math.exp(mean)
