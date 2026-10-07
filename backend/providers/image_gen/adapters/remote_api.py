"""远端图片生成 API 适配器骨架。"""
from __future__ import annotations
from backend.providers.image_gen.contracts import ImageGenRequest, ImageGenResult

class RemoteApiAdapter:
    def __init__(self, model_id: str, base_url: str, api_key: str = "") -> None:
        self.model_id = model_id
        self.base_url = base_url
        self.api_key = api_key
    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        raise NotImplementedError("RemoteApiAdapter.generate 待实装")
