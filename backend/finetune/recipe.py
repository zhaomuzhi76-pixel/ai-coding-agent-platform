"""Preset finetune recipes (LoRA variants + Prefix Tuning)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from backend.finetune.config import (
    FinetuneConfig, LoRAConfig, PrefixConfig,
)


@dataclass
class Recipe:
    name: str
    description: str
    build: object  # Callable[[str], FinetuneConfig]

    def create(self, base_model: str) -> FinetuneConfig:
        return self.build(base_model)

    def dump(self) -> dict:
        return {"name": self.name, "description": self.description}


def _lora_quick(base_model: str) -> FinetuneConfig:
    return FinetuneConfig(
        method="lora",
        base_model=base_model,
        num_epochs=2,
        batch_size=8,
        learning_rate=3e-4,
        lora=LoRAConfig(r=4, alpha=8, dropout=0.05),
    )


def _lora_balanced(base_model: str) -> FinetuneConfig:
    return FinetuneConfig(
        method="lora",
        base_model=base_model,
        num_epochs=3,
        batch_size=4,
        learning_rate=2e-4,
        lora=LoRAConfig(r=8, alpha=16, dropout=0.05),
    )


def _lora_quality(base_model: str) -> FinetuneConfig:
    return FinetuneConfig(
        method="lora",
        base_model=base_model,
        num_epochs=5,
        batch_size=2,
        learning_rate=1e-4,
        max_seq_len=4096,
        lora=LoRAConfig(
            r=32, alpha=64, dropout=0.1,
            target_modules=(
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ),
        ),
    )


def _prefix_tuning(base_model: str) -> FinetuneConfig:
    return FinetuneConfig(
        method="prefix",
        base_model=base_model,
        num_epochs=3,
        batch_size=4,
        learning_rate=3e-4,
        prefix=PrefixConfig(
            num_virtual_tokens=20,
            prefix_projection=True,
        ),
    )


RECIPES: Dict[str, Recipe] = {
    "lora-quick": Recipe(
        name="lora-quick",
        description="LoRA 快速试验：r=4, 2 epochs，适合小数据集探索",
        build=_lora_quick,
    ),
    "lora-balanced": Recipe(
        name="lora-balanced",
        description="LoRA 平衡：r=8, 3 epochs，默认推荐",
        build=_lora_balanced,
    ),
    "lora-quality": Recipe(
        name="lora-quality",
        description="LoRA 高质：r=32, 5 epochs，全 target modules",
        build=_lora_quality,
    ),
    "prefix-tuning": Recipe(
        name="prefix-tuning",
        description="Prefix Tuning：20 virtual tokens + projection",
        build=_prefix_tuning,
    ),
}


def list_recipes() -> List[str]:
    return sorted(RECIPES.keys())


def get_recipe(name: str) -> Recipe:
    if name not in RECIPES:
        raise KeyError(
            f"unknown recipe: {name} (available {list_recipes()})"
        )
    return RECIPES[name]


def build_config(recipe_name: str, base_model: str) -> FinetuneConfig:
    return get_recipe(recipe_name).create(base_model)


__all__ = [
    "Recipe", "RECIPES", "list_recipes", "get_recipe", "build_config",
]
