"""Job 分级器。按 PDF 页数分为 light/medium/heavy。
职责：只做分级，不做调度、不读文件内容、不查页数（页数由调用方传入）。
环境变量（可调阈值）：
  RAG_LIGHT_MAX_PAGES=50
  RAG_MEDIUM_MAX_PAGES=300
"""
from __future__ import annotations
import os
from typing import Literal

LEVEL_LIGHT: Literal["light"] = "light"
LEVEL_MEDIUM: Literal["medium"] = "medium"
LEVEL_HEAVY: Literal["heavy"] = "heavy"

_LIGHT = int(os.environ.get("RAG_LIGHT_MAX_PAGES", "50"))
_MEDIUM = int(os.environ.get("RAG_MEDIUM_MAX_PAGES", "300"))

def classify(page_count: int) -> str:
    """按页数返回级别。page_count<=0 视作 light（未知/小文件）。"""
    n = int(page_count or 0)
    if n <= _LIGHT:
        return LEVEL_LIGHT
    if n <= _MEDIUM:
        return LEVEL_MEDIUM
    return LEVEL_HEAVY

def thresholds() -> dict:
    return {"light_max_pages": _LIGHT, "medium_max_pages": _MEDIUM}

__all__ = ["classify", "thresholds",
           "LEVEL_LIGHT", "LEVEL_MEDIUM", "LEVEL_HEAVY"]
