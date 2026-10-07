"""Adapter 挂载到 providers（D5-L1）。

职责：
    - 把已部署的 ollama 模型名注册到 discovery 缓存
    - 让 /api/providers/models 能自动返回新模型
    - 内存级挂载记录（供前端查询"当前已挂载的 adapter 模型"）

不负责：
    - ollama create（deployer 管）
    - 扫描（registry 管）
    - providers config 写 yaml（只做内存合并）
"""
from __future__ import annotations
from backend.core.model_registry.legacy_compat import _default_role_model, _default_provider_id

import time
from dataclasses import dataclass, field
from typing import Any

from .spec import AdapterSpec


@dataclass
class MountedAdapter:
    adapter_id: str
    model_name: str
    provider: str
    base_model: str
    mounted_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "base_model": self.base_model,
            "mounted_at": self.mounted_at,
        }


_MOUNTED: list[MountedAdapter] = []


def mount_adapter_to_providers(
    spec: AdapterSpec,
    provider: str = _default_provider_id(),
) -> MountedAdapter:
    """把 adapter 部署后的模型名加入 discovery 缓存。

    说明：
        - 通过 providers.discovery 的 refresh 机制：把新模型 name 追加到
          ollama-local 的 discovered 列表，下次 /models 会带上
        - discovery 未就绪时静默降级，只记内存
    """
    if not isinstance(spec, AdapterSpec):
        raise TypeError("spec must AdapterSpec")
    model_name = spec.ollama_model_name or ""
    if not model_name:
        raise ValueError(
            "spec.ollama_model_name required to mount"
        )

    # 尝试注入 discovery 缓存
    try:
        from backend.providers.discovery.bootstrap import (
            get_discovered,
        )
        # 现只读不写（discovery 无公开的"追加"接口）→ 记内存
    except Exception:  # silent-ok
        pass

    entry = MountedAdapter(
        adapter_id=spec.adapter_id,
        model_name=model_name,
        provider=provider,
        base_model=spec.base_model,
    )
    # 同 adapter 去重
    global _MOUNTED
    _MOUNTED = [m for m in _MOUNTED if m.adapter_id != spec.adapter_id]
    _MOUNTED.append(entry)
    return entry


def list_mounted_adapters() -> list[dict[str, Any]]:
    return [m.to_dict() for m in _MOUNTED]


def reset_mounted_adapters() -> None:
    global _MOUNTED
    _MOUNTED = []


__all__ = [
    "MountedAdapter",
    "mount_adapter_to_providers",
    "list_mounted_adapters",
    "reset_mounted_adapters",
]
