"""Part 1 of agent_loop.py."""
from __future__ import annotations

import time

import asyncio

from typing import Any

from ..observation import render as render_observation

from ..prompt_builder import build_system_prompt, parse_action

from ..tool_registry import dispatch_tool

from ..approval_interceptor import maybe_intercept, DEFAULT_MODE

DEFAULT_MAX_STEPS = 10

LLM_CALL_TIMEOUT_SEC = 60

def _dedup_key(name: str, args: dict) -> str | None:
    """读/列类工具按路径去重；grep/count 按参数去重。"""
    if name in ("read_file", "list_dir"):
        p = args.get("path")
        return f"{name}:{p}" if isinstance(p, str) else None
    if name == "grep":
        p = args.get("pattern")
        e = args.get("ext", "")
        return f"grep:{p}:{e}" if isinstance(p, str) else None
    if name == "count_files":
        return f"count:{args.get('ext', '')}"
    return None
