"""进程级 RAG 治理挂载钩子。

由 backend/bootstrap.py 调用：
    bootstrap() → install_rag_governance()
    shutdown()  → uninstall_rag_governance()

设计：
    - 幂等（plugin.install 内部处理）
    - 失败不阻塞启动（try/except + log）
    - env 逃生门：RAG_GOVERNANCE=0 禁用
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

_ENV_KEY = "RAG_GOVERNANCE"
_FALSY = ("0", "false", "no", "off")


def _disabled() -> bool:
    return os.environ.get(_ENV_KEY, "1").strip().lower() in _FALSY


def install_rag_governance() -> Dict[str, Any]:
    """挂载 RAG 治理；失败不抛异常。"""
    if _disabled():
        logger.info("[rag-governance] 已禁用（%s=0）", _ENV_KEY)
        return {"status": "disabled"}
    try:
        from backend.rag.governance.plugin import install as _install
        result = _install()
        logger.info(
            "[rag-governance] %s patched=%s",
            result.get("status"), result.get("patched"),
        )
        return result
    except Exception:
        logger.exception("[rag-governance] 挂载失败（不阻塞启动）")
        return {"status": "error"}


def uninstall_rag_governance() -> None:
    """反挂载；失败不抛异常。"""
    try:
        from backend.rag.governance.plugin import uninstall as _uninstall
        _uninstall()
    except Exception:
        pass


__all__ = ["install_rag_governance", "uninstall_rag_governance"]
