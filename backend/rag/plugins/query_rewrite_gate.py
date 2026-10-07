"""查询改写门控插件 —— 环境变量集中管理。

职责：单一（is_enabled / model_name / describe）。
不实现改写逻辑本身，仅做门控决策。
"""
from __future__ import annotations
import os

_ENV_FLAG = "RAG_QUERY_REWRITE_ENABLED"
_ENV_MODEL = "RAG_QUERY_REWRITE_MODEL"
_DEFAULT_MODEL = "gemma3:latest"


def is_enabled() -> bool:
    """查询改写总开关（环境变量 RAG_QUERY_REWRITE_ENABLED）。"""
    v = os.environ.get(_ENV_FLAG, "0").strip().lower()
    return v in ("1", "true", "yes", "on")


def model_name() -> str:
    """返回改写所用模型名（带默认值兜底）。"""
    return os.environ.get(_ENV_MODEL, _DEFAULT_MODEL) or _DEFAULT_MODEL


def describe() -> dict:
    """返回门控状态字典（供 /status 端点使用）。"""
    return {"enabled": is_enabled(), "model": model_name()}
