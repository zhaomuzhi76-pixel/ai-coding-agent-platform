"""图片生成桥。职责：调 executor 出图并把 ImageGenResult 转为 ImageArtifact。
不做模型选择、不做重试、不做持久化。"""
from __future__ import annotations
from typing import Callable
from backend.providers.image_gen.contracts import ImageGenRequest, ImageGenResult
from backend.providers.image_gen.executor import execute
from backend.providers.multimodal.contracts import ImageArtifact, ImageSource
from backend.providers.selection.contracts import ModelDescriptor

ExecutorFn = Callable[[ModelDescriptor, ImageGenRequest], ImageGenResult]

class ImageGenBridge:
    def __init__(self, executor: ExecutorFn = execute) -> None:
        self._executor = executor

    def generate_image(self, descriptor: ModelDescriptor, prompt: str,
                 *, width: int = 512, height: int = 512) -> ImageArtifact:
        req = ImageGenRequest(prompt=prompt, width=width, height=height)
        res = self._executor(descriptor, req)
        url = str(res.meta.get("url", "") or "")
        alt = (prompt or "generated")[:80]
        aid = f"gen-{descriptor.id}"
        if url:
            return ImageArtifact(id=aid, mime=res.mime,
                                 source=ImageSource.GENERATED,
                                 url=url, alt_text=alt)
        return ImageArtifact(id=aid, mime=res.mime,
                             source=ImageSource.GENERATED,
                             b64=res.image_b64, alt_text=alt)
