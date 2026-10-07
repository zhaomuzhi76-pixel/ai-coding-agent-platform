"""Factory: build the MCP router for app assembly."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.mcp.binding import McpBinding
from backend.api.mcp.router import McpRouter


def build_mcp_router() -> APIRouter:
    return McpRouter(McpBinding()).router


__all__ = ["build_mcp_router"]
