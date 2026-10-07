"""模型名解析器（单一职责：探测 ollama + 大小写不敏感解析 + env 兜底）。

背景：
  · ollama 真名 'Gemma3:latest'（大写 G） vs 代码里 'gemma3:latest'
  · 直接命名会造成 404 → gateway 回退 → 日志噪音
  · 本模块集中处理：探测 / 解析 / 写 env

零硬编码：
  · 不出现任何具体模型名字面量
  · 默认值从 ollama /api/tags 动态获取
  · 全 env 可覆盖
"""
from __future__ import annotations
import json
import os
import urllib.request
from functools import lru_cache
from typing import Tuple

_ENV_HOST = "OLLAMA_HOST"
_ENV_QA_MODEL = "RAG_QA_MODEL"
_ENV_REWRITE_MODEL = "RAG_QUERY_REWRITE_MODEL"
_ENV_DEFAULT_ROLE = "RAG_DEFAULT_CHAT_ROLE"

# 非 chat 模型关键词（过滤用，纯语义关键词，非模型名）
# 非 chat 关键词（语义类别，非模型名）
_NON_CHAT_HINTS = (
    "embed", "rerank", "bge",          # 向量/重排
    "coder",                            # 代码模型
    "-v:", "vl:", "vision", "-vision",  # 视觉/多模态
    "minicpm-v", "llava",               # 已知视觉模型
)


def _host() -> str:
    return os.environ.get(_ENV_HOST, "http://127.0.0.1:11434").rstrip("/")


@lru_cache(maxsize=4)
def _probe() -> Tuple[str, ...]:
    """探测 ollama 本地模型列表（缓存；失败返回空元组）。"""
    try:
        req = urllib.request.Request(f"{_host()}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            d = json.loads(r.read().decode())
        return tuple(
            str(m.get("name", "")).strip()
            for m in d.get("models", []) if m.get("name")
        )
    except Exception:
        return ()


def list_available() -> Tuple[str, ...]:
    """只读返回当前可用模型名（缓存）。"""
    return _probe()


def clear_cache() -> None:
    """清空探测缓存（测试用）。"""
    _probe.cache_clear()


def resolve(name: str) -> str:
    """大小写不敏感解析；前缀匹配；找不到返回原名。"""
    if not name:
        return name
    target = name.lower()
    avail = _probe()

    for m in avail:
        if m.lower() == target:
            return m

    base = target.split(":", 1)[0]
    for m in avail:
        ml = m.lower()
        if ml == base or ml.startswith(base + ":"):
            return m
    return name


def _is_chat_like(name: str) -> bool:
    n = name.lower()
    return not any(h in n for h in _NON_CHAT_HINTS)


def default_chat_model() -> str:
    """从 env / ollama 探测一个默认 chat 模型。找不到返回空串。"""
    for env_key in ("RAG_DEFAULT_CHAT_MODEL", _ENV_QA_MODEL):
        v = os.environ.get(env_key)
        if v:
            return resolve(v)
    avail = _probe()
    for m in avail:
        if _is_chat_like(m):
            return m
    return ""


def bootstrap_env() -> bool:
    """把真实模型名写入标准 env（幂等；不覆盖已有值）。"""
    real = default_chat_model()
    if not real:
        return False
    os.environ.setdefault(_ENV_QA_MODEL, real)
    os.environ.setdefault(_ENV_REWRITE_MODEL, real)
    return True


def snapshot() -> dict:
    """只读诊断快照。"""
    return {
        "host": _host(),
        "available_count": len(_probe()),
        "available": list(_probe()),
        "qa_model_env": os.environ.get(_ENV_QA_MODEL, ""),
        "rewrite_model_env": os.environ.get(_ENV_REWRITE_MODEL, ""),
        "default_chat": default_chat_model(),
    }


# import 时自动写 env（幂等；不改已有环境）
try:
    bootstrap_env()
except Exception:
    pass
