"""响应组装。职责：把 text + ImageArtifact 序列组装为 MultimodalResponse。
不生成图片、不做 IO、不写盘。"""
from __future__ import annotations
from typing import Sequence
from backend.providers.multimodal.contracts import ImageArtifact, MultimodalResponse

def emit_text_only(text: str, llm_display: str = "",
                   output_mode: str = "text_only") -> MultimodalResponse:
    return MultimodalResponse(text=text, images=(),
                              meta={"llm": llm_display, "output_mode": output_mode})

def emit_with_artifacts(text: str, artifacts: Sequence[ImageArtifact],
                        llm_display: str = "",
                        output_mode: str = "llm_plus_image_gen") -> MultimodalResponse:
    imgs = tuple(artifacts)
    return MultimodalResponse(
        text=text, images=imgs,
        meta={"llm": llm_display, "output_mode": output_mode,
              "image_count": len(imgs)},
    )
