"""LoRA backend via HuggingFace peft — 真训练（4bit QLoRA）。

契约：
    - prepare: 加载 tokenizer + base model(4bit) + 应用 LoraConfig
    - train: 格式化样本 → Dataset → TrainingArguments → Trainer.train()
    - save: model.save_pretrained + tokenizer.save_pretrained

硬件：
    - CUDA 可用 → 4bit 量化 + bf16/fp16 混合精度
    - CUDA 不可用 → 回退 fp32 CPU（慢但能跑通流程）

不负责：
    - 数据加载（loader 管）
    - 事件推送（runner 管）
    - 目录约定（runner 设置 output_dir）
\n\nCompat shim. See ._peft_lora_parts."""
from __future__ import annotations
from ._peft_lora_parts import *  # noqa
from ._peft_lora_parts import (LoRABackend,)  # noqa
