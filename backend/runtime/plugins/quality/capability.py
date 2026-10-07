"""Quality 能力声明：供 runtime capability_loader 发现。"""
from __future__ import annotations

CAPABILITY = {
    "name": "quality",
    "version": "1.0.0",
    "provides": ["quality.one_shot_gate", "quality.registry"],
    "layer": "quality",
}
