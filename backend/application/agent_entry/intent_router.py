"""意图路由：判断用户消息属于哪类任务。

工业级契约（对齐 Codex / Claude Code 入口分层）：
    - query    : 只读查询（文件数、目录、统计）→ 不调 LLM
    - analyze  : 项目分析 → 走 LLM + 项目采样
    - modify   : 修改代码 → 走原 pipeline
    - create   : 新建项目/文件
"""
from __future__ import annotations

import re


class Intent:
    QUERY = "query"
    ANALYZE = "analyze"
    MODIFY = "modify"
    CREATE = "create"


_READONLY_MARKERS = re.compile(
    r"不要修改|不修改|只读|仅读|read-only|do\s+not\s+modify",
    re.IGNORECASE,
)

_QUERY_PATTERNS = (
    r"多少(个|条|行|处|种)?",
    r"几个",
    r"统计",
    r"文件数",
    r"文件列表",
    r"列出.{0,6}文件",
    r"how\s+many",
    r"count\b",
    r"list\s+files",
)

_ANALYZE_PATTERNS = (
    r"分析(这个|该|一下)?(项目|工程|代码|仓库|系统)",
    r"项目(结构|架构|概览|全貌)",
    r"在做什么",
    r"有什么用",
    r"是什么(项目|工程)",
    r"explain\s+(the\s+)?(project|codebase)",
    r"what\s+does\s+this",
)

_CREATE_PATTERNS = (
    r"新建(一个)?(项目|工程|文件|模块)",
    r"创建(一个)?(项目|工程|文件|模块)",
    r"create\s+(a\s+)?(project|app|file)",
    r"生成(一个)?(项目|工程)",
)

_MODIFY_PATTERNS = (
    r"修改|改(一下|成)|修复|fix\b",
    r"重构|refactor",
    r"添加|新增|加个|加一个",
    r"删除|去掉|移除",
    r"edit\b|modify\b",
)


def _match_any(patterns, text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def route(message: str) -> str:
    """返回 Intent 常量。空消息保守走 modify。"""
    if not isinstance(message, str) or not message.strip():
        return Intent.MODIFY
    text = message.strip()

    if _READONLY_MARKERS.search(text):
        return Intent.QUERY
    if _match_any(_QUERY_PATTERNS, text):
        return Intent.QUERY
    if _match_any(_CREATE_PATTERNS, text):
        return Intent.CREATE
    if _match_any(_ANALYZE_PATTERNS, text):
        return Intent.ANALYZE
    if _match_any(_MODIFY_PATTERNS, text):
        return Intent.MODIFY
    # 无明确修改意图 → 默认按"分析/对话"处理（走 LLM，语义准确）
    # 之前兜底 MODIFY 导致 "1+1=?" 被误标 modify
    return Intent.ANALYZE


__all__ = ["Intent", "route"]
