"""Bridge: attach a remote MCP endpoint's tools to a local ToolRuntime."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.mcp.client import McpClient
from backend.mcp.remote_tool import RemoteTool
from backend.runtime.tools.runtime import ToolRuntime


async def attach_remote(
    tool_runtime: ToolRuntime,
    client: McpClient,
    *,
    namespace: str = "mcp",
    include: List[str] = None,
) -> List[str]:
    """Initialize client, list remote tools, register them locally.

    Returns the list of registered local tool names.
    """
    await client.initialize()
    descriptors = await client.list_tools()
    include_set = set(include or [])
    registered: List[str] = []
    for desc in descriptors:
        raw_name = str(desc.get("name", ""))
        if include_set and raw_name not in include_set:
            continue
        tool = RemoteTool(client, desc, prefix=namespace)
        tool_runtime.register_tool(tool)
        registered.append(tool.name)
    return registered


__all__ = ["attach_remote"]
