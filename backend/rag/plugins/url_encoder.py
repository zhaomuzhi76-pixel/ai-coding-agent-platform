"""URL 编码插件 —— 带计数指标的 URL 编码。

职责：单一（encode_path / passthrough / snapshot / reset）。
不重复 retrieval_paths._to_url 的路径语义。
"""
from __future__ import annotations
from urllib.parse import quote

_METRICS = {"encoded": 0, "passthrough": 0, "empty": 0}


def encode_path(rel: str, safe: str = "/") -> str:
    """对路径段做 URL 编码（safe 保持路径分隔符）。"""
    if not rel:
        _METRICS["empty"] += 1
        return ""
    _METRICS["encoded"] += 1
    return quote(rel, safe=safe)


def passthrough(url: str) -> str:
    """直通未编码的整段 URL（计数用）。"""
    _METRICS["passthrough"] += 1
    return url


def snapshot() -> dict:
    """返回编码指标只读快照。"""
    return dict(_METRICS)


def reset() -> None:
    """清空所有计数（测试用）。"""
    for k in _METRICS:
        _METRICS[k] = 0
