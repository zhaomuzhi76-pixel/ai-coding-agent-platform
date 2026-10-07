"""评分器共用工具（避免 evaluator ↔ judges 循环依赖）"""
from __future__ import annotations

import json
import re


def ev(text: str) -> str:
    return (text or "").strip()[:200]


def extract_json(text: str) -> dict | None:
    """从响应里提取第一个合法 JSON 对象"""
    t = (text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t, re.I)
    if m:
        t = m.group(1).strip()
    start = t.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(t[start:i + 1])
                    return obj if isinstance(obj, dict) else None
                except Exception:
                    return None
    return None
