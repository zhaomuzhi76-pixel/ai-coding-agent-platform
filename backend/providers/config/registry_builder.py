"""Build CapabilityMatrix + ModelCatalog from LLM config.

职责：
    - LLMConfig → CapabilityMatrix（供路由）
    - LLMConfig → ModelCatalog（供前端读）
不负责：
    - 构造 provider 实例（那是 ProviderAssemblyBuilder 的职责）
"""
from __future__ import annotations

from typing import Dict, Optional

from backend.providers.config.loader import LLMConfig, load_llm_config
from backend.providers.routing.capability_matrix import (
    CapabilityMatrix,
    ModelCapability,
)
from backend.providers.routing.task_router import (
    ModelCatalog,
    ModelSelector,
)


def build_matrix(cfg: LLMConfig) -> CapabilityMatrix:
    matrix = CapabilityMatrix()
    for p in cfg.providers:
        for m in p.models:
            matrix.register(ModelCapability(
                model=m.id,
                provider=p.name,
                context_window=m.context_window,
                max_output=m.max_output,
                supports_tool_call=m.supports_tool_call,
                supports_stream=m.supports_stream,
                supports_embedding=m.supports_embedding,
                cost_input_per_1k=m.cost_input_per_1k,
                cost_output_per_1k=m.cost_output_per_1k,
                strengths=tuple(m.strengths),
            ))
    return matrix


def build_catalog(cfg: LLMConfig) -> ModelCatalog:
    matrix = build_matrix(cfg)
    catalog = ModelCatalog(matrix)
    for p in cfg.providers:
        for m in p.models:
            catalog.set_display_name(m.id, m.display_name)
    return catalog


def build_selector(
    cfg: LLMConfig, default_model: Optional[str] = None,
) -> ModelSelector:
    matrix = build_matrix(cfg)
    if default_model is None:
        # 选第一个模型的 id 作为默认
        first = cfg.all_models()
        default_model = first[0]["model"] if first else ""
    return ModelSelector(matrix, default_model=default_model)


def build_all(cfg: Optional[LLMConfig] = None) -> Dict:
    """One-liner: config → {matrix, catalog, selector}."""
    actual = cfg or load_llm_config()
    return {
        "config": actual,
        "matrix": build_matrix(actual),
        "catalog": build_catalog(actual),
        "selector": build_selector(actual),
    }


__all__ = [
    "build_matrix",
    "build_catalog",
    "build_selector",
    "build_all",
]
