"""统一静默吞异常日志入口（工业级）。

调用方：
    except Exception as e:
        swallow("模块.位置", e)                 # 默认 warn
        swallow("rag.persist", e, level="error") # 关键路径

环境变量：
    SILENT_DEBUG=1  开启 debug 级（默认不打印）
"""
from __future__ import annotations

import os
import sys
from typing import Final

_DEBUG: Final[bool] = os.environ.get("SILENT_DEBUG", "").lower() in ("1", "true", "yes")

_TAGS: Final[dict[str, str]] = {
    "debug": "·",
    "info":  "ℹ",
    "warn":  "⚠",
    "error": "✗",
}


def swallow(where: str, exc: BaseException, *, level: str = "warn") -> None:
    """统一记录被吞掉的异常。

    level 顺序（严重度递增）: debug < info < warn < error
    debug 级仅在 SILENT_DEBUG=1 时输出。
    """
    if level == "debug" and not _DEBUG:
        return
    tag = _TAGS.get(level, "·")
    try:
        print(
            f"[silent/{level}] {tag} {where}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        # silent 自身绝不抛异常
        pass


__all__ = ["swallow"]
