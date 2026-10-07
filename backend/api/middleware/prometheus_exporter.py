"""Prometheus 指标导出（单一职责：系统状态 → text/plain 格式）。

暴露指标：
  biancheng_up                       进程存活
  biancheng_uptime_seconds           进程运行时长
  biancheng_middleware_enabled       中间件开关
  biancheng_middleware_max_concurrent 并发上限
  biancheng_middleware_timeout_s     排队超时
  biancheng_middleware_whitelist_count 白名单路径数
  biancheng_rag_ready                RAG 就绪（0/1）
  biancheng_filesystem_workspace_ready 工作区可用（0/1）

不做：监控告警、聚合、存储。
"""
from __future__ import annotations
import os
import time
from typing import List

_START = time.time()


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _whitelist_count() -> int:
    raw = os.environ.get("RAG_MW_WHITELIST_PATHS", "")
    return len([x for x in raw.split(",") if x.strip()])


def _rag_ready() -> int:
    """探测 RAG 服务（不依赖 fastapi）。"""
    try:
        import urllib.request
        port = _env_int("BACKEND_PORT", 9022)
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/api/rag/status", timeout=2) as r:
            return 1 if r.status == 200 else 0
    except Exception:
        return 0


def _workspace_ready() -> int:
    """工作区根存在性（env RAG_FS_WORKSPACE_ROOT）。"""
    root = os.environ.get("RAG_FS_WORKSPACE_ROOT", "")
    if not root:
        return 1  # 未配置视为就绪（agent 走默认路径）
    return 1 if os.path.isdir(root) else 0


def render() -> str:
    """返回 Prometheus text/plain 格式。"""
    lines: List[str] = []

    def m(name: str, help_: str, type_: str, val) -> None:
        lines.append(f"# HELP {name} {help_}")
        lines.append(f"# TYPE {name} {type_}")
        lines.append(f"{name} {val}")
        lines.append("")

    m("biancheng_up", "1 if process is up", "gauge", 1)
    m("biancheng_uptime_seconds", "Process uptime in seconds", "gauge",
      f"{time.time() - _START:.3f}")
    m("biancheng_middleware_enabled", "1 if concurrency middleware enabled",
      "gauge", 1 if _env_bool("RAG_MW_ENABLED") else 0)
    m("biancheng_middleware_max_concurrent", "Max concurrent requests",
      "gauge", _env_int("RAG_MW_MAX_CONCURRENT", 8))
    m("biancheng_middleware_timeout_s", "Queue timeout in seconds",
      "gauge", _env_float("RAG_MW_TIMEOUT_S", 30.0))
    m("biancheng_middleware_whitelist_count", "Whitelist path count",
      "gauge", _whitelist_count())
    m("biancheng_rag_ready", "1 if RAG service ready", "gauge", _rag_ready())
    m("biancheng_filesystem_workspace_ready",
      "1 if configured workspace root exists", "gauge", _workspace_ready())

    return "\n".join(lines)


def build_metrics_route(app) -> bool:
    """幂等挂 /metrics 路由。返回是否首次挂载。"""
    if getattr(app, "_prom_metrics_installed", False):
        return False
    app._prom_metrics_installed = True
    try:
        from fastapi.responses import PlainTextResponse

        @app.get("/metrics", include_in_schema=False)
        async def _metrics():
            return PlainTextResponse(
                render(),
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )
        return True
    except Exception:
        return False


__all__ = ["render", "build_metrics_route"]
