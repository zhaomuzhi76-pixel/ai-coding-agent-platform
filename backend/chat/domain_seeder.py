"""把领域 provider 数据 + 图片 URL 索引进 Chroma（幂等）。

设计：
    - 数据（图片 URL / 字段标签）→ backend/data/*.json
    - 通过 backend/config/rag_governance 读取（env 可覆盖阈值）
    - 支持向后兼容：`IMAGE_URLS` / `_LABELS` 由模块 __getattr__ 动态返回
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.config.rag_governance import get_rag_config

logger = logging.getLogger(__name__)


# ── 配置访问（动态，支持 env 更新 + cache_clear 后 reload）──

def _domain_images() -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """动态读图片表（backend/data/rag_domain_images.json）。"""
    return get_rag_config().domain_images


def _field_labels() -> Dict[str, str]:
    """动态读字段中文标签（backend/data/rag_field_labels.json）。"""
    return get_rag_config().field_labels


# ── 向后兼容：旧名字 `IMAGE_URLS` / `_LABELS` 动态代理 ──

def __getattr__(name: str) -> Any:
    if name == "IMAGE_URLS":
        return get_rag_config().domain_images
    if name == "_LABELS":
        return get_rag_config().field_labels
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ── 渲染 / 索引 ──

def _render_entity_text(entity: Any) -> str:
    labels = _field_labels()
    parts = [entity.name]
    for k, v in (entity.attributes or {}).items():
        if isinstance(v, (list, tuple)):
            v = "、".join(str(x) for x in v)
        elif isinstance(v, dict):
            v = ", ".join(f"{kk}={vv}" for kk, vv in v.items())
        parts.append(f"{labels.get(k, k)}:{v}")
    return "。".join(parts)


def _build_items(domain: str, provider: Any) -> List[Dict[str, Any]]:
    urls = _domain_images().get(domain, {})
    out: List[Dict[str, Any]] = []
    for et in provider.list_entity_types():
        for name in provider.list_entities(et):
            entity = provider.lookup_entity(et, name)
            if entity is None:
                continue
            out.append({
                "text": _render_entity_text(entity),
                "source": f"domain:{domain}:{et}",
                "source_path": f"domain/{domain}/{et}",
                "images": urls.get(entity.name, []),
                "metadata": {"domain": domain, "entity_type": et,
                             "entity_name": entity.name,
                             "kb": domain},
            })
    return out


def seed_domain(domain: str, *, service: Any = None,
                force: bool = False) -> Dict[str, Any]:
    """幂等：领域实体 + 图 URL → Chroma。"""
    from backend.domain.providers import AgricultureProvider, FinanceProvider
    providers = {"agriculture": AgricultureProvider, "finance": FinanceProvider}
    if domain not in providers:
        return {"status": "unknown_domain", "domain": domain,
                "available": sorted(providers.keys())}
    provider = providers[domain]()

    if service is None:
        from backend.api.rag.multimodal_runtime import get_multimodal_rag_runtime
        service = get_multimodal_rag_runtime().service

    items = _build_items(domain, provider)
    if not items:
        return {"status": "empty", "domain": domain}

    report = service.index_items(items)
    indexed = getattr(report, "indexed", 0)
    chunks = getattr(report, "chunks", 0)
    imgs = sum(len(it["images"]) for it in items)
    logger.info("[seed] domain=%s items=%d images=%d indexed=%d",
                domain, len(items), imgs, indexed)
    return {
        "status": "ok", "domain": domain,
        "items": len(items), "images": imgs,
        "indexed": indexed, "chunks": chunks,
    }


__all__ = ["seed_domain", "_domain_images", "_field_labels",
           "_render_entity_text", "_build_items"]
