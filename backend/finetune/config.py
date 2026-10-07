"""Finetune configuration dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LoRAConfig:
    r: int = 8
    alpha: int = 16
    dropout: float = 0.05
    target_modules: tuple = (
        "q_proj", "k_proj", "v_proj", "o_proj",
    )
    bias: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "r": self.r, "alpha": self.alpha,
            "dropout": self.dropout,
            "target_modules": list(self.target_modules),
            "bias": self.bias,
        }


@dataclass
class PrefixConfig:
    num_virtual_tokens: int = 20
    prefix_projection: bool = False
    encoder_hidden_size: int = 1024

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_virtual_tokens": self.num_virtual_tokens,
            "prefix_projection": self.prefix_projection,
            "encoder_hidden_size": self.encoder_hidden_size,
        }


@dataclass
class FinetuneConfig:
    method: str = "lora"
    base_model: str = ""
    output_dir: str = "./finetune_out"
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    max_seq_len: int = 2048
    warmup_ratio: float = 0.03
    save_steps: int = 200
    logging_steps: int = 20
    lora: Optional[LoRAConfig] = None
    prefix: Optional[PrefixConfig] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "method": self.method,
            "base_model": self.base_model,
            "output_dir": self.output_dir,
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "max_seq_len": self.max_seq_len,
            "warmup_ratio": self.warmup_ratio,
            "save_steps": self.save_steps,
            "logging_steps": self.logging_steps,
        }
        if self.lora:
            base["lora"] = self.lora.to_dict()
        if self.prefix:
            base["prefix"] = self.prefix.to_dict()
        if self.extra:
            base["extra"] = dict(self.extra)
        return base
