"""Ollama 模型自动发现 → ModelSpec 字典列表。"""
from __future__ import annotations

from typing import Any

from .classifier import (
    is_embedding_model,
    is_reranker_model,
    should_include_as_chat,
)
from .ollama_client import fetch_ollama_models


def _to_display_name(model_id: str) -> str:
    """qwen3:8b → Qwen3 8B；qwen2.5-coder:7b → Qwen2.5 Coder 7B"""
    base, _, tag = model_id.partition(":")
    parts = (
        base.replace("-", " ").replace(".", " ")
        .replace("_", " ").split()
    )
    pretty = " ".join(
        p.capitalize() if not p[0].isdigit() else p
        for p in parts if p
    )
    if tag:
        pretty += " " + (tag.upper() if tag[0].isalpha() else tag)
    return pretty or model_id


def _to_spec_dict(m: dict[str, Any]) -> dict[str, Any]:
    name = str(m.get("name", "")).strip()
    details = m.get("details", {}) or {}
    ctx = int(details.get("context_length", 0) or 0) or 32768
    is_emb = is_embedding_model(name, details)
    is_rr = is_reranker_model(name)
    return {
        "id": name,
        "display_name": name,
        "context_window": ctx,
        "max_output": 8192,
        "supports_tool_call": not (is_emb or is_rr),
        "supports_stream": not (is_emb or is_rr),
        "supports_embedding": is_emb,
        "cost_input_per_1k": 0.0,
        "cost_output_per_1k": 0.0,
        "strengths": (
            ["local"]
            + (["embedding"] if is_emb else [])
            + (["rerank"] if is_rr else [])
            + (["chat"] if not is_emb and not is_rr else [])
        ),
    }


async def discover_ollama_models(
    base_url: str,
    *,
    include_embedding: bool = False,
    include_reranker: bool = False,
) -> list[dict[str, Any]]:
    """发现 Ollama 的所有模型。

    默认只返回 chat 模型；include_* 可开启 embedding / reranker。
    """
    raw = await fetch_ollama_models(base_url)
    out: list[dict[str, Any]] = []
    for m in raw:
        name = str(m.get("name", "")).strip()
        if not name:
            continue
        details = m.get("details", {}) or {}
        if is_embedding_model(name, details) and not include_embedding:
            continue
        if is_reranker_model(name) and not include_reranker:
            continue
        if not should_include_as_chat(name, details):
            continue
        out.append(_to_spec_dict(m))
    return out


__all__ = ["discover_ollama_models"]
