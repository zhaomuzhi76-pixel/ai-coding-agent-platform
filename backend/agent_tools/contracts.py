"""Agent 工具契约。职责：只描述数据类 + 序列化。
不注册、不执行、不调 MCP。与 backend/mcp/* 边界：
mcp 管协议层（tools/list, tools/call）；本模块管 Agent 侧"我要挂哪些工具"。"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

class ToolCategory(str, Enum):
    RAG = "rag"
    DOMAIN = "domain"
    IMAGE = "image"
    DOC = "doc"
    RESEARCH = "research"
    WEB = "web"
    CODE = "code"
    MISC = "misc"

class ToolDomain(str, Enum):
    GENERAL = "general"
    TCM = "tcm"
    AGRICULTURE = "agriculture"
    FINANCE = "finance"

@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    category: ToolCategory
    domain: ToolDomain = ToolDomain.GENERAL
    server: str = "local"
    tags: tuple = ()
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))
        if not self.name.strip(): raise ValueError("ToolDescriptor.name required")
        if not self.description.strip():
            raise ValueError("ToolDescriptor.description required")
        if not isinstance(self.tags, tuple):
            raise TypeError("tags must be tuple")

@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    call_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments",
                           MappingProxyType(dict(self.arguments)))
        if not self.name.strip(): raise ValueError("ToolCall.name required")

@dataclass(frozen=True)
class ToolResult:
    name: str
    ok: bool
    output: str = ""
    error: str = ""
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "meta", MappingProxyType(dict(self.meta)))

    def to_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok,
                "output": self.output, "error": self.error,
                "meta": dict(self.meta)}

__all__ = ["ToolCategory", "ToolDomain", "ToolDescriptor",
           "ToolCall", "ToolResult"]
