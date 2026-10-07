"""中间件配置（单一职责：集中参数，全部 env 可覆盖，零硬编码）。

环境变量（全部可选，默认值为合理兜底）：
  RAG_MW_ENABLED                  总开关（默认 0）
  RAG_MW_MAX_CONCURRENT           并发上限（默认 8）
  RAG_MW_TIMEOUT_S                排队超时秒（默认 30.0）
  RAG_MW_RETRY_AFTER_MIN_S        Retry-After 下限（默认 1）
  RAG_MW_RETRY_AFTER_MAX_S        Retry-After 上限（默认 60）
  RAG_MW_RETRY_AFTER_FALLBACK_S   无历史数据时单次耗时估值（默认 8）
  RAG_MW_RETRY_HINT_TEMPLATE      提示模板（默认 "retry after {seconds}s"）
  RAG_MW_WHITELIST_PATHS          免限流路径前缀（逗号分隔）
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Tuple


def _env_int(name: str, default: int, min_val: int = 1) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return max(min_val, int(raw))
    except ValueError:
        return default


def _env_float(name: str, default: float, min_val: float = 0.001) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return max(min_val, float(raw))
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw


def _env_csv(name: str, default: Tuple[str, ...]) -> Tuple[str, ...]:
    raw = os.environ.get(name)
    if not raw:
        return default
    return tuple(x.strip() for x in raw.split(",") if x.strip())


@dataclass(frozen=True)
class MWConfig:
    enabled: bool
    max_concurrent: int
    timeout_s: float
    retry_after_min_s: int
    retry_after_max_s: int
    retry_after_fallback_s: int
    retry_hint_template: str
    whitelist_paths: Tuple[str, ...]


def load() -> MWConfig:
    """从环境变量装载（无状态，每次调用返回新对象）。"""
    return MWConfig(
        enabled=_env_bool("RAG_MW_ENABLED", False),
        max_concurrent=_env_int("RAG_MW_MAX_CONCURRENT", 8),
        timeout_s=_env_float("RAG_MW_TIMEOUT_S", 30.0, min_val=0.1),
        retry_after_min_s=_env_int("RAG_MW_RETRY_AFTER_MIN_S", 1),
        retry_after_max_s=_env_int("RAG_MW_RETRY_AFTER_MAX_S", 60),
        retry_after_fallback_s=_env_int("RAG_MW_RETRY_AFTER_FALLBACK_S", 8),
        retry_hint_template=_env_str("RAG_MW_RETRY_HINT_TEMPLATE",
                                     "retry after {seconds}s"),
        whitelist_paths=_env_csv(
            "RAG_MW_WHITELIST_PATHS",
            ("/health", "/api/rag/status", "/api/rag/metrics",
             "/docs", "/openapi.json"),
        ),
    )


def snapshot(cfg: MWConfig) -> dict:
    """只读快照（供 /status 或测试展示）。"""
    return {
        "enabled": cfg.enabled,
        "max_concurrent": cfg.max_concurrent,
        "timeout_s": cfg.timeout_s,
        "retry_after_min_s": cfg.retry_after_min_s,
        "retry_after_max_s": cfg.retry_after_max_s,
        "retry_after_fallback_s": cfg.retry_after_fallback_s,
        "retry_hint_template": cfg.retry_hint_template,
        "whitelist_paths": list(cfg.whitelist_paths),
    }
