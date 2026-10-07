"""生产入口：env 驱动启用 multiplex team，零侵入默认路径。

契约：
  - env LOCO_MULTIPLEX_TEAM 未设 / 空 → 所有入口返回 None → 上层走原路径
  - env 有值 → 解析为 role_specs，构造全局单例 team
  - env 变化 → 自动重建 team
  - 线程安全（进程内单例）

env 格式（JSON）：
  LOCO_MULTIPLEX_TEAM=[
      {"name": "planner", "model_chain": [[_default_provider_id(), "qwen3:8b"]]},
      {"name": "coder",   "model_chain": [[_default_role_model("code"), _default_role_model("code")]]}
  ]

不负责：
  - WS / HTTP 传输
  - 协议 / 进程管理
  - 编排逻辑（现有 AgentRuntime 管）
"""
from __future__ import annotations
from backend.core.model_registry.legacy_compat import _default_role_model, _default_provider_id

import json
import os
import threading

from .factory import MultiplexTeam, build_multiplex_runtime

ENV_KEY = "LOCO_MULTIPLEX_TEAM"

_team: MultiplexTeam | None = None
_built_raw: str | None = None
_lock = threading.Lock()


def _raw_env() -> str | None:
    raw = os.environ.get(ENV_KEY, "").strip()
    return raw or None


def load_team_spec() -> list | None:
    raw = _raw_env()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, list) or not data:
        return None
    return data


def get_or_build_team() -> MultiplexTeam | None:
    global _team, _built_raw
    with _lock:
        raw = _raw_env()
        if not raw:
            _team = None
            _built_raw = None
            return None
        if _team is not None and _built_raw == raw:
            return _team
        spec = load_team_spec()
        if spec is None:
            return None
        _team = build_multiplex_runtime(spec)
        _built_raw = raw
        return _team


async def run_team_if_configured(payload: dict) -> dict | None:
    """env 未配置返回 None（信号"未启用"）；否则跑 chain 并返回结果。"""
    team = get_or_build_team()
    if team is None:
        return None
    message = str(payload.get("message", ""))
    session_id = str(payload.get("session_id", "") or "") or "team-auto"
    try:
        results = await team.run_chain(message, session_id=session_id)
    except Exception as exc:
        return {
            "multiplex": True,
            "session_id": session_id,
            "success": False,
            "error": type(exc).__name__ + ": " + str(exc),
        }
    return {
        "multiplex": True,
        "session_id": session_id,
        "success": True,
        "roles": list(team.role_names),
        "steps": [
            {"role": r.role, "content": r.content}
            for r in results
        ],
        "final": results[-1].content if results else "",
    }


async def shutdown_team() -> None:
    global _team, _built_raw
    with _lock:
        team = _team
        _team = None
        _built_raw = None
    if team is not None:
        await team.shutdown()


def reset_team() -> None:
    """测试用：清掉单例（不 shutdown，由调用方决定）。"""
    global _team, _built_raw
    with _lock:
        _team = None
        _built_raw = None


__all__ = [
    "ENV_KEY",
    "load_team_spec",
    "get_or_build_team",
    "run_team_if_configured",
    "shutdown_team",
    "reset_team",
]
