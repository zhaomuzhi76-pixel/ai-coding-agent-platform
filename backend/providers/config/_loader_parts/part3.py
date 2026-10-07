"""Part 3 of loader.py."""
from __future__ import annotations
from .part1 import (Any, Optional, Path, _DEFAULT_PATH, os, yaml,)  # noqa
from .part1 import EmbeddingSpec  # noqa
from .part1 import RerankerSpec  # noqa
from .part1 import VectorStoreSpec  # noqa
from .part2 import LLMConfig  # noqa
from .part2 import _parse_provider  # noqa
from .part2 import _parse_routing  # noqa

def _parse_embedding(raw: Any) -> Optional[EmbeddingSpec]:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name", "")).strip()
    prov = str(raw.get("provider", "")).strip()
    model = str(raw.get("model", "")).strip()
    if not name or not prov or not model:
        return None
    return EmbeddingSpec(
        name=name, provider=prov, model=model,
        dimension=int(raw.get("dimension", 0)),
        is_default=bool(raw.get("default", False)),
    )

def _parse_reranker(raw: Any) -> Optional[RerankerSpec]:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name", "")).strip()
    prov = str(raw.get("provider", "")).strip()
    model = str(raw.get("model", "")).strip()
    if not name or not prov or not model:
        return None
    return RerankerSpec(
        name=name, provider=prov, model=model,
        is_default=bool(raw.get("default", False)),
    )

def _parse_vector_store(raw: Any) -> VectorStoreSpec:
    if not isinstance(raw, dict):
        return VectorStoreSpec()
    return VectorStoreSpec(
        driver=str(raw.get("driver", "chroma")).strip(),
        path=str(raw.get("path", "./vector_db")).strip(),
        collection=str(raw.get("collection", "code_index")).strip(),
        default_embedding=str(
            raw.get("default_embedding", "")
        ).strip(),
        default_reranker=str(
            raw.get("default_reranker", "")
        ).strip(),
        top_k=int(raw.get("top_k", 10)),
        rerank_top_k=int(raw.get("rerank_top_k", 5)),
    )

def load_llm_config(path: Optional[Path] = None) -> LLMConfig:
    target = path or Path(os.environ.get(
        "LLM_PROVIDERS_FILE", str(_DEFAULT_PATH),
    ))
    if not target.is_file():
        return LLMConfig(source=str(target), skipped=["file_not_found"])

    with target.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    providers_raw = data.get("providers", []) or []
    cfg = LLMConfig(source=str(target))
    for raw in providers_raw:
        if not isinstance(raw, dict):
            continue
        spec = _parse_provider(raw)
        if spec is None:
            pname = str(raw.get("name", "<unknown>"))
            cfg.skipped.append(pname)
            continue
        cfg.providers.append(spec)

    cfg.default_provider = str(
        data.get("default_provider", "") or ""
    ).strip()
    if not cfg.default_provider and cfg.providers:
        cfg.default_provider = cfg.providers[0].name

    cfg.default_model = str(
        data.get("default_model", "") or ""
    ).strip()
    if not cfg.default_model and cfg.providers:
        for p in cfg.providers:
            if p.name == cfg.default_provider and p.models:
                cfg.default_model = p.models[0].id
                break

    cfg.agent_routing = _parse_routing(
        data.get("agent_routing"), cfg.providers,
    )

    # Embedding / Reranker 只保留 provider 已注册的
    provider_names = {p.name for p in cfg.providers}
    cfg.embeddings = [
        e for e in (
            _parse_embedding(x)
            for x in (data.get("embeddings") or [])
        )
        if e is not None and e.provider in provider_names
    ]
    cfg.rerankers = [
        r for r in (
            _parse_reranker(x)
            for x in (data.get("rerankers") or [])
        )
        if r is not None and r.provider in provider_names
    ]
    cfg.vector_store = _parse_vector_store(
        data.get("vector_store"),
    )
    return cfg

__all__ = [
    "ModelSpec", "ProviderSpec", "ModelRef",
    "EmbeddingSpec", "RerankerSpec", "VectorStoreSpec",
    "LLMConfig", "load_llm_config",
]
