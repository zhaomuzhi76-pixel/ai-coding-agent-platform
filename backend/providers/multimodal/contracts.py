"""
多模态响应契约层。

职责边界（不可扩展）：
  - 描述"文字 + 图片同时返回"的唯一响应包结构
  - 校验图片来源与载荷
  - 不生成图片、不调模型、不管流式
上游：providers.selection.contracts
下游：chatbot 插件的 artifact_emitter、L3 response_assembler、L4 API 层
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple


class ImageSource(str, Enum):
    """图片来源三态，前端据此决定渲染策略。"""
    GENERATED = "generated"
    RETRIEVED = "retrieved"
    INPUT_ECHO = "input_echo"


@dataclass(frozen=True)
class ImageArtifact:
    """单张图片产物。url 与 b64 二选一，避免响应体歧义。"""
    id: str
    mime: str
    source: ImageSource
    url: Optional[str] = None
    b64: Optional[str] = None
    alt_text: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not self.id:
            raise ValueError("ImageArtifact.id must not be empty")
        if not self.mime:
            raise ValueError("ImageArtifact.mime must not be empty")
        if not self.mime.startswith("image/"):
            raise ValueError(f"ImageArtifact.mime must be image/*, got {self.mime!r}")
        if self.url and self.b64:
            raise ValueError("ImageArtifact: url and b64 are mutually exclusive")
        if not self.url and not self.b64:
            raise ValueError("ImageArtifact: either url or b64 must be provided")


@dataclass(frozen=True)
class MultimodalResponse:
    """
    chatbot 的唯一响应契约。
    约束：即使只有文字，images 也必须为 tuple（可为空），前端只走一条渲染路径。
    """
    text: str
    images: Tuple[ImageArtifact, ...] = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not isinstance(self.text, str):
            raise TypeError("MultimodalResponse.text must be str")
        if not isinstance(self.images, tuple):
            raise TypeError(
                "MultimodalResponse.images must be tuple, "
                "not list — 防止下游原地修改破坏不可变性"
            )
        for img in self.images:
            if not isinstance(img, ImageArtifact):
                raise TypeError(
                    f"MultimodalResponse.images entries must be ImageArtifact, "
                    f"got {type(img).__name__}"
                )

    @property
    def has_images(self) -> bool:
        return len(self.images) > 0

    def with_extra_image(self, artifact: ImageArtifact) -> "MultimodalResponse":
        return MultimodalResponse(
            text=self.text,
            images=self.images + (artifact,),
            meta=self.meta,
        )
