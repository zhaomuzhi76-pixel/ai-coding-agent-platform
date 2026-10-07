"""Provider assembly configuration.

清理后：只保留 yaml 路径覆盖。provider 细节全在 yaml。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderAssemblyConfiguration:
    """Minimal config: yaml path override only.

    provider 名字、模型、endpoint、key 全部在
    backend/config/llm_providers.yaml。
    """

    yaml_path: str = ""

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "yaml_path": self.yaml_path or "<default>",
        }


__all__ = [
    "ProviderAssemblyConfiguration",
]
