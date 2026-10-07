"""Built-in message packs."""
from __future__ import annotations

from typing import List

from backend.i18n.catalog import MessageCatalog
from backend.i18n.locale import EN_US, ZH_CN
from backend.i18n.message import Message

ZH_MESSAGES: List[Message] = [
    Message(key="app.name", text="智能编程助手"),
    Message(key="app.greeting", text="你好，{user}"),
    Message(key="error.not_found", text="未找到：{resource}"),
    Message(key="error.permission", text="权限不足：{tool}"),
    Message(key="error.timeout", text="操作超时：{op}"),
    Message(key="tool.running", text="正在执行工具：{name}"),
    Message(key="tool.done", text="工具完成：{name}（{duration}ms）"),
    Message(key="domain.crop", text="作物"),
    Message(key="domain.stock", text="股票"),
    Message(key="finetune.started", text="微调开始，方法={method}，样本={count}"),
    Message(key="finetune.finished", text="微调完成，保存到 {path}"),
    Message(key="mcp.connected", text="已连接 MCP 服务：{name}"),
    Message(key="agent.planner", text="规划中…"),
    Message(key="agent.coder", text="编码中…"),
    Message(key="agent.reviewer", text="审查中…"),
]

EN_MESSAGES: List[Message] = [
    Message(key="app.name", text="AI Coding Assistant"),
    Message(key="app.greeting", text="Hello, {user}"),
    Message(key="error.not_found", text="Not found: {resource}"),
    Message(key="error.permission", text="Permission denied: {tool}"),
    Message(key="error.timeout", text="Operation timed out: {op}"),
    Message(key="tool.running", text="Running tool: {name}"),
    Message(key="tool.done", text="Tool completed: {name} ({duration}ms)"),
    Message(key="domain.crop", text="Crop"),
    Message(key="domain.stock", text="Stock"),
    Message(key="finetune.started",
            text="Finetune started: method={method}, samples={count}"),
    Message(key="finetune.finished",
            text="Finetune finished, saved to {path}"),
    Message(key="mcp.connected", text="Connected to MCP server: {name}"),
    Message(key="agent.planner", text="Planning…"),
    Message(key="agent.coder", text="Coding…"),
    Message(key="agent.reviewer", text="Reviewing…"),
]


def load_builtin(catalog: MessageCatalog) -> None:
    catalog.register_many(ZH_CN, ZH_MESSAGES)
    catalog.register_many(EN_US, EN_MESSAGES)


__all__ = ["ZH_MESSAGES", "EN_MESSAGES", "load_builtin"]
