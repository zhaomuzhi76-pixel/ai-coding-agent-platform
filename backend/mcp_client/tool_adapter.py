"""MCP 远端工具 → agent_tools 工具描述符 适配器。
职责：把 SessionManager 的 RouteTarget/RemoteToolDesc 翻译成 ToolDescriptor。
不做执行（executor_provider 管）、不注册（registry 管）、不连 server（session_manager 管）。"""
from __future__ import annotations
from typing import Optional

from backend.agent_tools.contracts import (
    ToolCategory, ToolDescriptor, ToolDomain)
from backend.mcp_client.contracts import RemoteToolDesc
from backend.mcp_client.session_manager import RouteTarget

DEFAULT_CATEGORY = ToolCategory.MISC
DEFAULT_DOMAIN = ToolDomain.GENERAL

_CATEGORY_BY_KEYWORD = (
    ("image", "img", "picture", "photo", "screenshot", "draw", "render"),
    ("doc", "pdf", "word", "docx", "pptx", "excel", "xlsx", "spreadsheet"),
    ("research", "arxiv", "paper", "scholar", "citation"),
    ("web", "fetch", "browser", "http", "url", "search", "crawl"),
    ("code", "file", "fs", "shell", "git", "read_file", "write_file"),
)

def _guess_category(raw_name: str, desc: str) -> ToolCategory:
    blob = f"{raw_name} {desc}".lower()
    for keywords, cat in (
        (("image", "img", "picture", "photo", "screenshot", "draw"), ToolCategory.IMAGE),
        (("pdf", "docx", "pptx", "xlsx", "word", "excel", "powerpoint", "spreadsheet"), ToolCategory.DOC),
        (("arxiv", "paper", "scholar", "citation"), ToolCategory.RESEARCH),
        (("browser", "fetch", "crawl", "http"), ToolCategory.WEB),
        (("file", "fs.", "shell", "git", "read_file", "write_file"), ToolCategory.CODE),
    ):
        if any(k in blob for k in keywords):
            return cat
    return DEFAULT_CATEGORY

def _guess_domain(raw_name: str, desc: str) -> ToolDomain:
    blob = f"{raw_name} {desc}".lower()
    if any(k in blob for k in ("tcm", "中医", "中药", "穴位", "经络")):
        return ToolDomain.TCM
    if any(k in blob for k in ("agri", "农业", "作物", "施肥", "农药")):
        return ToolDomain.AGRICULTURE
    if any(k in blob for k in ("finance", "金融", "股票", "基金", "保险")):
        return ToolDomain.FINANCE
    return DEFAULT_DOMAIN

def remote_to_descriptor(
    desc: RemoteToolDesc,
    *,
    category: Optional[ToolCategory] = None,
    domain: Optional[ToolDomain] = None,
) -> ToolDescriptor:
    """RemoteToolDesc → ToolDescriptor。
    分类/领域优先用调用方传入；未传则按名字/描述启发式推断。"""
    cat = category or _guess_category(desc.raw_name, desc.description)
    dom = domain or _guess_domain(desc.raw_name, desc.description)
    return ToolDescriptor(
        name=desc.namespaced_name,
        description=desc.description or desc.raw_name,
        category=cat,
        domain=dom,
        server=desc.server_id,
        tags=("mcp", desc.server_id),
        meta={
            "raw_name": desc.raw_name,
            "server_id": desc.server_id,
            "input_schema": dict(desc.input_schema),
        },
    )

def route_to_descriptor(
    target: RouteTarget,
    *,
    description: str = "",
    category: Optional[ToolCategory] = None,
    domain: Optional[ToolDomain] = None,
) -> ToolDescriptor:
    """RouteTarget → ToolDescriptor（描述可选，从 name 兜底）。"""
    return ToolDescriptor(
        name=target.namespaced_name,
        description=description or target.raw_name,
        category=category or _guess_category(target.raw_name, description),
        domain=domain or _guess_domain(target.raw_name, description),
        server=target.server_id,
        tags=("mcp", target.server_id),
        meta={"raw_name": target.raw_name, "server_id": target.server_id},
    )

__all__ = ["remote_to_descriptor", "route_to_descriptor",
           "DEFAULT_CATEGORY", "DEFAULT_DOMAIN"]
