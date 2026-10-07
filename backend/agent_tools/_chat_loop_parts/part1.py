"""Part 1 of chat_loop.py."""
from __future__ import annotations

import asyncio

import json

import re

from dataclasses import dataclass, field

from typing import Any, Mapping, Optional

from backend.agent_tools.contracts import ToolCall, ToolResult, ToolDescriptor

from backend.agent_tools.executor import ToolExecutor

from backend.agent_tools.registry import ToolRegistry

from backend.agent_tools.session import SessionHistory, get_default_history

DEFAULT_MAX_TOOL_STEPS = 4  # [BUG4_FIX] 4 步足够

DEFAULT_TIMEOUT = 60.0

SYSTEM_TEMPLATE = """你是知识型 AI 助手，用中文简洁、准确回答。

可用工具（仅在有明确需要时调用，**不要反复调用**）：
{tools}

工作原则（**严格遵守**）：
1. **证据优先**：如果消息里包含【系统已自动检索知识库，以下为证据】，请**直接基于证据回答**；只有证据明显不足时才调用工具补充。
2. **不重复调用**：同一工具同一参数只调一次；调过一次无结果就换思路或直接说明。
3. **拒绝编造**：证据里没有的信息**不要编**，明确说"暂无法回答"。
4. **一轮即答**：如果 message 里已有【系统已自动检索知识库】，直接回答，不要再调工具。
4. **步骤上限**：最多 {max_steps} 步，用完必须给出最终答案。

[IMG_INTENT]
**图片意图（重要）**：
- 用户说"给我看 X"、"X 的图片"、"X 长什么样"、"显示图片"、"看图" → 调用 `image.search_by_text`，参数 `{{"query": "<药材/主题>"}}`
- image 工具**只调一次**；返回空说"图片库无此内容"，**禁止改 query 重试**
- 若消息里**已有【系统已自动检索知识库，以下为证据】含图片**，则**直接基于图片回答**，不再调 image 工具

**防循环（硬性）**：
- 同一工具同一 query **只能调一次**（无论成功失败）
- 调过一次无结果，**立即 done=true 总结**，不得再调
- 严禁编造 query（如把"人参"改成"人参味苦平"去重试）

[PREFER_IMG]
**中药材名问句优先调 image.search_by_text**
- 用户问句包含"<药材名>是什么"、"<药材名>的功效"、"介绍<药材名>" 等
- → **必须**先调用 `image.search_by_text` 拿图（参数 query 用当前药材名）
- 然后再基于图 + rag.search_tcm 文本综合回答
- ❌ 严禁只调 rag.search_tcm 而返回 0 张图

[CTX_LOCAL]
**图片意图必须用当前消息的原词**
- 当用户问 "X长什么样"、"给我看X的图片" 时，image.search_by_text 的 query **必须包含当前消息里的 X**
- ❌ 严禁沿用上轮对话的主题词（上轮问人参，本轮问芍药 → 必须用芍药）
- 正确：{{'query': '芍药'}}  错误：{{'query': '人参'}}（这是上轮的词）

[NO_PLACEHOLDER]
**action 字段严禁使用占位符**
- action 必须是真实工具名（如 rag.search_tcm / image.search_by_text）
- 严禁抄示例里的占位符（如 '工具名'）
- 严禁使用中文占位符

输出协议（**必须**严格按 JSON）：
  {{"action": "工具名", "args": {{...}}}}   ← 需要调工具
  {{"done": true, "answer": "最终答案"}}    ← 完成任务

只输出 JSON，不要解释、不要 markdown。"""

_JSON_RE = re.compile(r"<tool_call>\s*(\{[\s\S]*?\})\s*</tool_call>", re.I)

_CODE_RE = re.compile(r"```[a-zA-Z]*\s*([\s\S]*?)\s*```")

def _specs_text(registry: ToolRegistry) -> str:
    ds = registry.all()
    if not ds:
        return "（无可用工具）"
    return "\n".join(f"- {d.name}: {d.description}" for d in ds)

def _build_system(registry: ToolRegistry, max_steps: int) -> str:
    return SYSTEM_TEMPLATE.format(tools=_specs_text(registry),
                                   max_steps=max_steps)

def _iter_json_objects(text: str):
    """按文本顺序枚举所有 balanced JSON 对象。"""
    n = len(text)
    i = 0
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth, in_str, esc = 0, False, False
        closed = False
        for j in range(i, n):
            ch = text[j]
            if in_str:
                if esc: esc = False
                elif ch == "\\": esc = True
                elif ch == '"': in_str = False
                continue
            if ch == '"': in_str = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    raw = text[i:j + 1]
                    try:
                        o = json.loads(raw)
                        if isinstance(o, dict):
                            yield o
                    except json.JSONDecodeError:
                        pass
                    i = j + 1
                    closed = True
                    break
        if not closed:
            i += 1

def _extract_json(text: str) -> Optional[dict]:
    text = (text or "").strip()
    if not text:
        return None

    # 1) <tool_call>...</tool_call> 优先
    m = _JSON_RE.search(text)
    if m:
        try:
            o = json.loads(m.group(1))
            if isinstance(o, dict):
                return o
        except json.JSONDecodeError:
            pass

    # 2) 收集所有 balanced JSON（文本顺序）
    objs = list(_iter_json_objects(text))

    # 3) **工具调用优先**：有 action 立即返回（ReAct 铁律：先工具）
    for o in objs:
        act = o.get("action")
        if isinstance(act, str) and act.strip():
            return o

    # 4) 无 action 再看 done
    for o in objs:
        if o.get("done") is True:
            return o

    # 5) code block 兜底
    m = _CODE_RE.search(text)
    if m:
        try:
            o = json.loads(m.group(1).strip())
            if isinstance(o, dict):
                return o
        except json.JSONDecodeError:
            pass

    return None

@dataclass(frozen=True)
class ChatTurnResult:
    session_id: str
    answer: str
    tool_trace: tuple = ()
    steps: int = 0
    ok: bool = True
    error: str = ""
    images: tuple = ()   # [MM] 图文同返
    images: tuple = ()   # [MM] 图文同返
