"""能力声明。职责：只描述本插件提供什么，不含任何业务逻辑。"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, FrozenSet, Mapping

PLUGIN_ID = "chatbot"
PLUGIN_VERSION = "0.1.0"

DEFAULT_CAPABILITIES: FrozenSet[str] = frozenset({
    "chat.text",
    "chat.multimodal_input",
    "chat.multimodal_output",
    "chat.domain_route",
    "chat.selection_binding",
})

@dataclass(frozen=True)
class CapabilitySpec:
    plugin_id: str
    version: str
    capabilities: FrozenSet[str]
    meta: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not self.plugin_id: raise ValueError("plugin_id must not be empty")
        if not self.capabilities: raise ValueError("capabilities must not be empty")

    @classmethod
    def default(cls) -> "CapabilitySpec":
        return cls(plugin_id=PLUGIN_ID, version=PLUGIN_VERSION,
                   capabilities=DEFAULT_CAPABILITIES, meta={})

    def has(self, name: str) -> bool:
        return name in self.capabilities
