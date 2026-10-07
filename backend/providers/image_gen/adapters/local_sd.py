"""本地扩散模型适配器骨架。实装走插件或新增 adapter，不在此文件塞网络代码。"""
from __future__ import annotations
from backend.providers.image_gen.contracts import ImageGenRequest, ImageGenResult

class LocalSDAdapter:
    def __init__(self, model_id: str, endpoint: str = "http://127.0.0.1:7860") -> None:
        self.model_id = model_id
        self.endpoint = endpoint
    def generate(self, request: ImageGenRequest) -> ImageGenResult:
        raise NotImplementedError("LocalSDAdapter.generate 待实装")
