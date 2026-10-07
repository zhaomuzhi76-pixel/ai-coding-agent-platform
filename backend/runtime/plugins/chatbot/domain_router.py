"""领域路由。职责：按关键词把用户文本分派到金融/农业/中医/general。

数据源：backend/data/rag_domain_keywords.json（不硬编码）
不负责：lookup / 检索 / domain provider 实现。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from backend.config.rag_governance import get_rag_config


# ── 向后兼容：旧名字 `DOMAIN_KEYWORDS` / `DOMAIN_TOOLS` 动态代理 ──

def __getattr__(name: str):
    if name == "DOMAIN_KEYWORDS":
        return {k: tuple(v) for k, v in get_rag_config().domain_keywords.items()}
    if name == "DOMAIN_TOOLS":
        return {k: tuple(v) for k, v in get_rag_config().domain_tools.items()}
    if name == "GENERAL_DOMAIN":
        return get_rag_config().general_domain
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@dataclass(frozen=True)
class RouteDecision:
    domain: str
    matched_keywords: Tuple[str, ...]
    tools: Tuple[str, ...]


def _score(text: str, keywords: Tuple[str, ...]) -> Tuple[str, ...]:
    return tuple(k for k in keywords if k in text)


def route_domain(text: str) -> RouteDecision:
    """按关键词命中数决定领域；无命中回退 general。"""
    cfg = get_rag_config()
    general = cfg.general_domain
    tools_map = cfg.domain_tools
    general_tools = tuple(tools_map.get(general, ("chat",)))

    if not text:
        return RouteDecision(general, (), general_tools)

    hits: List[Tuple[int, str, Tuple[str, ...]]] = []
    for domain, kws in cfg.domain_keywords.items():
        matched = _score(text, tuple(kws))
        if matched:
            hits.append((len(matched), domain, matched))

    if not hits:
        return RouteDecision(general, (), general_tools)

    hits.sort(key=lambda x: (-x[0], x[1]))
    _, domain, matched = hits[0]
    tools = tuple(tools_map.get(domain, ("domain_lookup", "domain_search")))
    return RouteDecision(domain, matched, tools)


__all__ = ["RouteDecision", "route_domain"]
