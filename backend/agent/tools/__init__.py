"""Agent tools namespace (thin re-export).

冻结层提供全部工具基础设施：
    core.tools.schema                -> ToolSchema / ToolParameter
    core.tools.result_contract       -> ToolResult / ToolResultProtocol
    core.tools.runtime_tool_protocol -> RuntimeToolProtocol
    runtime.tools.registry           -> ToolRegistry
    runtime.tools.runtime            -> ToolRuntime
本包只 re-export 冻结层能力，不重造任何东西。
"""
from backend.core.tools.schema import ToolParameter, ToolSchema
from backend.core.tools.result_contract import (
    ToolResult,
    ToolResultProtocol,
)
from backend.core.tools.runtime_tool_protocol import RuntimeToolProtocol
from backend.runtime.tools.registry import ToolRegistry
from backend.runtime.tools.runtime import ToolRuntime

__all__ = [
    "ToolParameter",
    "ToolSchema",
    "ToolResult",
    "ToolResultProtocol",
    "RuntimeToolProtocol",
    "ToolRegistry",
    "ToolRuntime",
]
