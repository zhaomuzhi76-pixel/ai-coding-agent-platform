"""Agent 入口层。"""
from .intent_router import Intent, route
from .query_handler import handle_query
from .agent_entry import dispatch

__all__ = ["Intent", "route", "handle_query", "dispatch"]
