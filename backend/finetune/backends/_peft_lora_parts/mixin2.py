"""Mixin 2 of LoRABackend."""
from __future__ import annotations
from .part1 import (Any, Path,)  # noqa: F401
class _Mixin2:
    def save(self, artifact: Any, output_dir: str) -> None:
        if not isinstance(artifact, dict):
            raise TypeError("artifact must dict")
        trained = artifact.get("trained_model") or artifact.get("model")
        tokenizer = artifact.get("tokenizer")
        if trained is None:
            raise RuntimeError("no trained model to save")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        trained.save_pretrained(output_dir)
        if tokenizer is not None:
            tokenizer.save_pretrained(output_dir)

    def dump(self) -> dict:
        return {
            "name": self.name,
            "ready": self.ready(),
            "available": self.available(),
            "note": "4bit QLoRA via peft+transformers+bitsandbytes",
        }
