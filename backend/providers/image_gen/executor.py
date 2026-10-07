"""图片生成执行分发。职责：按 descriptor.provider 选择 adapter 并执行。
不做重试、不做缓存、不组装响应。"""
from __future__ import annotations
from typing import Optional
from backend.providers.image_gen.adapters.dashscope_adapter import DashScopeImageAdapter
from backend.providers.image_gen.adapters.local_sd import LocalSDAdapter
from backend.providers.image_gen.adapters.remote_api import RemoteApiAdapter
from backend.providers.image_gen.contracts import ImageGenRequest, ImageGenResult
from backend.providers.selection.contracts import ModelDescriptor

def _provider_of(descriptor: ModelDescriptor) -> str:
    return (descriptor.provider or "").lower()

def execute(descriptor: ModelDescriptor, request: ImageGenRequest,
            *, endpoint: Optional[str] = None,
            api_key: Optional[str] = None) -> ImageGenResult:
    p = _provider_of(descriptor)
    if p == "dashscope" or p == "aliyun":
        return DashScopeImageAdapter(model_id=descriptor.id,
                                     api_key=api_key).generate(request)
    if p == "local" or p == "local_sd" or p == "a1111":
        return LocalSDAdapter(model_id=descriptor.id,
                              endpoint=endpoint or "http://127.0.0.1:7860").generate(request)
    if p == "remote_api" or p == "openai":
        if not endpoint:
            raise RuntimeError(f"{descriptor.display_name} 需要 endpoint")
        return RemoteApiAdapter(model_id=descriptor.id,
                                base_url=endpoint, api_key=api_key or "").generate(request)
    raise RuntimeError(f"未知 provider：{descriptor.provider}")
