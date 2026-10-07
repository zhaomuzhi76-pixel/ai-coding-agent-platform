"""图片生成契约。"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional

@dataclass(frozen=True)
class ImageGenRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    seed: Optional[int] = None
    meta: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not self.prompt: raise ValueError("prompt must not be empty")
        if self.width <= 0 or self.height <= 0: raise ValueError("width/height must be > 0")

@dataclass(frozen=True)
class ImageGenResult:
    image_b64: str
    mime: str
    meta: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not self.image_b64: raise ValueError("image_b64 must not be empty")
        if not self.mime.startswith("image/"): raise ValueError("mime must be image/*")
