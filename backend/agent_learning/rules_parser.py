"""L2 .rules 文件解析器。

只做"文本 → Rule 列表"，不做存储、不做冲突检测。
"""
from __future__ import annotations

import re
from pathlib import Path

from backend.agent_learning.rules_contract import (
    KEY_TO_KIND, Rule, ParseResult,
)

# 支持的行格式：
#   key=value        （默认 kind 从 KEY_TO_KIND 推断）
#   kind.key=value   （显式 kind）
#   key: value       （YAML 风格冒号）
_LINE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*[:=]\s*(.+?)\s*$"
)
_COMMENT_PREFIXES = ("#", "//")


def parse_text(text: str, *, source: str = "") -> ParseResult:
    result = ParseResult(source_path=source)
    if not text:
        return result

    for i, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in _COMMENT_PREFIXES):
            continue

        m = _LINE_RE.match(line)
        if not m:
            result.errors.append(f"line {i}: 无法解析 {line[:60]!r}")
            continue

        key_path = m.group(1).strip()
        value = m.group(2).strip().strip("\"'")
        if not value:
            result.errors.append(f"line {i}: 空值 {key_path!r}")
            continue

        kind, key = _split_key(key_path)
        result.rules.append(Rule(
            kind=kind, key=key, value=value,
            line_no=i, source=source,
        ))

    return result


def parse_file(path: Path) -> ParseResult:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        r = ParseResult(source_path=str(path))
        r.errors.append(f"read error: {e}")
        return r
    return parse_text(text, source=str(path))


def _split_key(key_path: str) -> tuple[str, str]:
    """把 'code_style.forbid' 拆成 (kind, key)；'forbid' → ('code_style', 'forbid')。"""
    if "." in key_path:
        head, tail = key_path.split(".", 1)
        return head.strip(), tail.strip()
    return KEY_TO_KIND.get(key_path, "code_style"), key_path


__all__ = ["parse_text", "parse_file"]
