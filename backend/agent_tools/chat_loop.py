"""多轮对话 Agent Loop。职责：一轮对话内的工具调用 ReAct + 跨轮上下文累积。
不调 MCP 协议（executor/bridge 管）、不注册工具（registry 管）、不切分文档（rag 管）。
与 application/agent_loop 边界：那层是编程任务 ReAct；本层是多领域对话 ReAct。\n\nCompat shim. See ._chat_loop_parts."""
from __future__ import annotations
from ._chat_loop_parts import *  # noqa
from ._chat_loop_parts import (Any, ChatTurnResult, DEFAULT_MAX_TOOL_STEPS, DEFAULT_TIMEOUT, Mapping, Optional, SYSTEM_TEMPLATE, SessionHistory, ToolCall, ToolDescriptor, ToolExecutor, ToolRegistry, ToolResult, _CODE_RE, _JSON_RE, __all__, _build_system, _extract_json, _iter_json_objects, _specs_text, annotations, asyncio, dataclass, field, get_default_history, json, re, run_chat_turn,)  # noqa
