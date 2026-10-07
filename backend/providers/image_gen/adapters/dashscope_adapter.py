"""阿里云通义万相图片生成适配器。职责：真调 DashScope 出图。
不做选择、不组装响应、不写盘（图片以 URL 返回）。"""
from __future__ import annotations
import os
from backend.providers.image_gen.contracts import ImageGenRequest, ImageGenResult

DEFAULT_MODEL = "wanx2.1-t2i-turbo"

class DashScopeImageAdapter:
    def __init__(self, model_id: str = DEFAULT_MODEL,
                 api_key: str | None = None) -> None:
        self.model_id = model_id
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")

    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 未设置")
        try:
            import dashscope  # type: ignore
            from dashscope import ImageSynthesis  # type: ignore
        except ImportError as e:
            raise RuntimeError("未安装 dashscope SDK：pip install dashscope") from e
        dashscope.api_key = self.api_key
        size = f"{request.width}*{request.height}"
        rsp = ImageSynthesis.call(
            model=self.model_id, prompt=request.prompt,
            n=1, size=size)
        if rsp.status_code != 200:
            raise RuntimeError(f"DashScope 失败 {rsp.status_code}: {rsp.message}")
        out = rsp.output or {}
        results = out.get("results") or []
        if not results:
            raise RuntimeError("DashScope 未返回图片")
        url = results[0].get("url", "")
        if not url:
            raise RuntimeError("DashScope 返回无 url")
        return ImageGenResult(image_b64="", mime="image/png",
                              meta={"url": url, "model": self.model_id,
                                    "provider": "dashscope"})
