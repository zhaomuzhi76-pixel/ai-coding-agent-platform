"""RAG 模型配置：向量模型 + 重排序模型下拉数据源"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/rag", tags=["rag-config"])

CONFIG_PATH = Path(os.path.expanduser("~/.biancheng/rag_config.json"))

EMBED_TOKENS = ("embed", "embedding", "bge-m3", "nomic-embed", "mxbai-embed")
RERANK_TOKENS = ("rerank", "reranker", "bge-rerank", "gte-rerank")


def _load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_config(data: Dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _match(id_: str, display: str, tokens) -> bool:
    low = (id_ + " " + (display or "")).lower()
    return any(t in low for t in tokens)


@router.get("/config-options")
async def config_options() -> Dict[str, Any]:
    """返回配置中心里已验证的向量模型 + 重排序模型清单"""
    try:
        from backend.core.model_registry.registry import get_registry
        reg = get_registry()
    except Exception as e:
        return {"ok": False, "error": str(e),
                "embeddings": [], "rerankers": []}

    verified = set(reg.verification.list_verified())
    embeddings: List[Dict[str, Any]] = []
    rerankers: List[Dict[str, Any]] = []

    for m in reg.models.values():
        # 本地模型自动纳入；云端要求 verified
        prov = reg.providers.get(m.provider_id)
        is_local = prov and prov.kind in (
            "ollama", "local", "ollama-local", "vllm", "lmstudio")
        if not is_local and m.id not in verified:
            continue

        item = {
            "id": m.id,
            "provider": m.provider_id,
            "display_name": m.display_name or m.id,
            "is_local": bool(is_local),
        }
        if _match(m.id, m.display_name, EMBED_TOKENS):
            embeddings.append(item)
        if _match(m.id, m.display_name, RERANK_TOKENS):
            rerankers.append(item)

    # 兜底：本地 Ollama 里带 embedding 能力的直接扫一遍
    if not embeddings:
        try:
            import json as _json
            import urllib.request
            with urllib.request.urlopen(
                "http://127.0.0.1:11434/api/tags", timeout=3
            ) as r:
                tags = _json.loads(r.read())
            for m in tags.get("models", []):
                if "embedding" in m.get("capabilities", []):
                    embeddings.append({
                        "id": m["name"],
                        "provider": "ollama-local",
                        "display_name": m["name"],
                        "is_local": True,
                    })
        except Exception:
            pass

    return {
        "ok": True,
        "embeddings": embeddings,
        "rerankers": rerankers,
        "current": _load_config(),
    }


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    cfg = _load_config()
    # 补齐 idle_history_days 默认值
    if "idle_history_days" not in cfg:
        cfg["idle_history_days"] = 60
    return {"ok": True, "config": cfg}


# [VALID_KEYS] 只允许这些 key 被写（防注入/污染）
_ALLOWED_CONFIG_KEYS = {
    "embedding_model", "reranker_model", "reranker_enabled",
    "top_k", "vector_weight", "bm25_weight",
    "idle_history_days",
    "pipeline_enabled",
}


@router.post("/config")
async def set_config(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Merge 语义：只更新 payload 里显式给出的白名单 key，其他保留。"""
    cfg = _load_config()
    updated = []
    for k, v in (payload or {}).items():
        if k in _ALLOWED_CONFIG_KEYS:
            cfg[k] = v
            updated.append(k)
    _save_config(cfg)
    return {"ok": True, "config": cfg, "updated": updated}
