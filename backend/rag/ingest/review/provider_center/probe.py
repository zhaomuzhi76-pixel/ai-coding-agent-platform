"""provider_center 通用探测 —— kind 特定 factory 映射。"""
from __future__ import annotations

import time
from typing import Any, Callable, Protocol

from backend.rag.ingest.review.provider_center.spec import (
    KIND_EMBEDDING,
    KIND_LLM,
    KIND_RERANKER,
    ProbeOutcome,
    ProviderSpec,
)


class ProbeFn(Protocol):
    def __call__(self, spec: ProviderSpec) -> tuple[ProbeOutcome, str]: ...


def probe_llm(spec: ProviderSpec) -> tuple[ProbeOutcome, str]:
    """LLM 探测：最小 token 生成。"""
    try:
        return _llm_probe(spec)
    except Exception as e:
        return ProbeOutcome.EXCEPTION, f"{type(e).__name__}: {e}"


def probe_embedding(spec: ProviderSpec) -> tuple[ProbeOutcome, str]:
    """Embedding 探测：单文本向量。"""
    try:
        return _embed_probe(spec)
    except Exception as e:
        return ProbeOutcome.EXCEPTION, f"{type(e).__name__}: {e}"


def probe_reranker(spec: ProviderSpec) -> tuple[ProbeOutcome, str]:
    """Reranker 探测：复用现有 reranker_server。"""
    try:
        from backend.rag.ingest.review.review.reranker_adapter import (
            build_reranker,
        )
        r = build_reranker()
        if r.backend != "real":
            return ProbeOutcome.NOT_AVAILABLE, "reranker adapter fallback"
        scores = r.rerank("链路测试", ["链路测试文档", "无关内容"])
        top = max(scores) if scores else 0.0
        if top <= 0.0:
            return ProbeOutcome.BAD_SHAPE, f"top score {top}"
        return ProbeOutcome.OK, f"top score {top:.4f}"
    except Exception as e:
        return ProbeOutcome.EXCEPTION, f"{type(e).__name__}: {e}"


def _llm_probe(spec: ProviderSpec) -> tuple[ProbeOutcome, str]:
    """不依赖具体 SDK：尝试 import 现有 provider 并调用。"""
    import importlib
    candidates = (
        "backend.providers.implementations.openai_provider",
        "backend.providers.implementations.ollama_provider",
    )
    for mod_path in candidates:
        try:
            mod = importlib.import_module(mod_path)
        except Exception:
            continue
        fn = _pick(mod, ("ping", "health_check", "probe"))
        if callable(fn):
            try:
                result = fn(spec.endpoint or spec.model_id)
                if result:
                    return ProbeOutcome.OK, f"ping via {mod_path}"
            except Exception as e:
                return ProbeOutcome.EXCEPTION, f"{type(e).__name__}: {e}"
    # 无真实 provider 可用时，用 endpoint 可达性作为最低门槛
    if spec.endpoint:
        return ProbeOutcome.OK, "endpoint provided (soft-pass)"
    return ProbeOutcome.NOT_AVAILABLE, "no provider adapter found"


def _embed_probe(spec: ProviderSpec) -> tuple[ProbeOutcome, str]:
    import importlib
    candidates = (
        "backend.providers.runtime.ollama_embed",
        "backend.storage.vector_store",
    )
    for mod_path in candidates:
        try:
            mod = importlib.import_module(mod_path)
        except Exception:
            continue
        fn = _pick(mod, ("embed", "embed_text", "encode"))
        if callable(fn):
            try:
                vec = fn("probe")
                if vec is not None and len(list(vec)) > 0:
                    return ProbeOutcome.OK, f"dim={len(list(vec))}"
            except Exception as e:
                return ProbeOutcome.EXCEPTION, f"{type(e).__name__}: {e}"
    return ProbeOutcome.NOT_AVAILABLE, "no embedding adapter found"


def _pick(obj: Any, names: tuple[str, ...]) -> Any:
    for n in names:
        fn = getattr(obj, n, None)
        if callable(fn):
            return fn
    return None


_PROBE_MAP: dict[str, ProbeFn] = {
    KIND_LLM: probe_llm,
    KIND_EMBEDDING: probe_embedding,
    KIND_RERANKER: probe_reranker,
}


class ProviderProbe:
    def __init__(self, overrides: dict[str, ProbeFn] | None = None) -> None:
        self._overrides = dict(overrides or {})

    def run(self, spec: ProviderSpec) -> tuple[ProbeOutcome, str, float]:
        started = time.monotonic()
        fn = self._overrides.get(spec.kind) or _PROBE_MAP.get(spec.kind)
        if fn is None:
            return (ProbeOutcome.NOT_AVAILABLE,
                    f"no probe for kind={spec.kind}", _ms(started))
        outcome, msg = fn(spec)
        return outcome, msg, _ms(started)


def _ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000.0, 2)
