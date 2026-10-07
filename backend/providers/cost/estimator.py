"""Token 估算（无 provider 真 usage 时的兜底）。

规则：中文 ~1.5 字符/token，英文 ~4 字符/token，平均取 3。
真实 usage 接入后此模块不再使用，保留接口。
"""
from __future__ import annotations

from typing import Any, List


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / 3.0))


def estimate_messages(messages: List[Any]) -> int:
    total = 0
    for m in messages:
        if isinstance(m, dict):
            total += estimate_tokens(str(m.get("content", "")))
        else:
            total += estimate_tokens(str(m))
    return total


__all__ = ["estimate_tokens", "estimate_messages"]
