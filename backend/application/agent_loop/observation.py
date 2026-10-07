"""工具结果 → LLM 可读的观察文本。

工业级契约：
  - 单条观察 ≤ 2500 字符（够 LLM 看到 3~5 段关键代码）
  - 明确标注类型（FILE / LIST / GREP / COUNT）
  - 出错时结构清晰（ERROR + 原因）
"""
from __future__ import annotations

import json
from typing import Any

_MAX_CHARS = 2500


def render(result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        return f"OBSERVATION: {result!r}"
    if not result.get("ok", True):
        return f"ERROR: {result.get('error', 'unknown')}"

    # 文件内容
    if "content" in result:
        content = str(result.get("content", ""))
        size = result.get("size", len(content))
        path = result.get("path", "?")
        if len(content) > _MAX_CHARS:
            head = content[:_MAX_CHARS]
            return (
                f"FILE {path} ({size} bytes, 已截断至 {_MAX_CHARS} 字符):\n"
                f"{head}\n...(内容已截断)"
            )
        return f"FILE {path} ({size} bytes):\n{content}"

    # grep 命中
    if "hits" in result:
        hits = result.get("hits", [])
        lines = "\n".join(hits) if hits else "(无匹配)"
        return (
            f"GREP '{result.get('pattern', '')}' "
            f"命中 {result.get('count', 0)} 处:\n{lines}"
        )

    # 目录列表
    if "entries" in result:
        entries = result.get("entries", [])
        return f"LIST {result.get('path', '.')}:\n" + "\n".join(entries)

    # 计数
    if "exit_code" in result:
        cmd = result.get("command", "")
        code = result.get("exit_code", -1)
        out = str(result.get("stdout", "")).strip()
        err = str(result.get("stderr", "")).strip()
        parts = [f"COMMAND {cmd!r} (exit={code})"]
        if out:
            parts.append(f"STDOUT:\n{out}")
        if err:
            parts.append(f"STDERR:\n{err}")
        return "\n".join(parts)

    if "matched" in result:
        return (
            f"COUNT ext='{result.get('ext', '')}' "
            f"matched={result['matched']} total={result['total']}"
        )

    return "OBSERVATION: " + json.dumps(result, ensure_ascii=False)[:_MAX_CHARS]


__all__ = ["render"]
