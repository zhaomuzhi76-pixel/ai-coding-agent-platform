"""Prefix Tuning backend (peft wrapper · 真训练).

契约与 LoRABackend 一致：
    - prepare: 加载 tokenizer + base model + apply PrefixTuningConfig
    - train(artifact, samples, on_progress=None): HF Trainer
    - save(artifact, output_dir): model.save_pretrained

硬件：
    - CUDA 可用 → 4bit 量化 + bf16/fp16
    - 否则 → fp32 CPU
\n\nCompat shim. See ._prefix_tuning_parts."""
from __future__ import annotations
from ._prefix_tuning_parts import *  # noqa
from ._prefix_tuning_parts import (PrefixTuningBackend,)  # noqa
