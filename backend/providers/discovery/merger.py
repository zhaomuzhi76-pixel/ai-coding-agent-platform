"""把发现的模型合并到 LLMConfig（不修改原对象）。"""
from __future__ import annotations

from typing import Any

from backend.providers.config.loader import (
    LLMConfig,
    ModelSpec,
    ProviderSpec,
)


def _dict_to_model_spec(d: dict[str, Any]) -> ModelSpec:
    return ModelSpec(
        id=d["id"],
        display_name=d["display_name"],
        context_window=d["context_window"],
        max_output=d["max_output"],
        supports_tool_call=d["supports_tool_call"],
        supports_stream=d["supports_stream"],
        supports_embedding=d["supports_embedding"],
        cost_input_per_1k=d["cost_input_per_1k"],
        cost_output_per_1k=d["cost_output_per_1k"],
        strengths=list(d.get("strengths", [])),
    )


def merge_into_config(
    cfg: LLMConfig,
    discovered: dict[str, list[dict[str, Any]]],
) -> LLMConfig:
    """discovered: {provider_name: [model_dict, ...]}

    规则：
      - 保留 yaml 里声明的模型（元数据更精细）
      - 追加 discovery 发现的、yaml 里没有的
      - 返回新 LLMConfig，原对象不变
    """
    if not discovered:
        return cfg

    new_providers: list[ProviderSpec] = []
    for p in cfg.providers:
        extra = discovered.get(p.name)
        if not extra:
            new_providers.append(p)
            continue

        existing_ids = {m.id for m in p.models}
        merged_models = list(p.models)
        for d in extra:
            if d["id"] in existing_ids:
                continue
            merged_models.append(_dict_to_model_spec(d))

        new_providers.append(ProviderSpec(
            name=p.name,
            type=p.type,
            display_name=p.display_name,
            base_url=p.base_url,
            api_key=p.api_key,
            models=merged_models,
        ))

    return LLMConfig(
        providers=new_providers,
        skipped=list(cfg.skipped),
        source=cfg.source,
        default_provider=cfg.default_provider,
        default_model=cfg.default_model,
        agent_routing=dict(cfg.agent_routing),
        embeddings=list(cfg.embeddings),
        rerankers=list(cfg.rerankers),
        vector_store=cfg.vector_store,
    )


__all__ = ["merge_into_config"]
