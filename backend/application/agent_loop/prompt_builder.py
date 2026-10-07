"""每轮 prompt 构造 + LLM 响应解析。

兼容三种 LLM 输出格式（工业级做法）：
  1. Qwen 系列原生 <tool_call>{...}</tool_call> XML 标签
  2. Markdown 代码块包裹的 JSON
  3. 纯 JSON / 多段 JSON 中的最终决定
"""
from __future__ import annotations

import json
import re
from typing import Any

from .tool_registry import specs


SYSTEM_TEMPLATE = """你是一个自主编程 Agent。通过调用工具完成任务。

可用工具：
{tools}

工作区：{workspace}

工作流程（ReAct 模式）：
1. 思考当前状态
2. 输出 ONE 动作
3. 收到工具结果
4. 重复直到完成

**输出格式**（严格遵循，一次只输出一个动作）：
调用工具：{{"thought": "思考", "action": "工具名", "args": {{"参数名": "值"}}}}
任务完成：{{"thought": "总结", "done": true, "answer": "最终回答（中文）"}}

**收敛规则（必须遵守）**：
- 读取 3~4 个关键文件后，必须开始总结
- 已读过的文件**不要重复读**
- 信息足够回答问题时，立刻用 done=true 结束
- 最多 {max_steps} 步；第 {max_steps} 步前必须输出 done=true
- 不要为"追求完美"而无限读文件

[OBS_TRUST]
**信任 observation**：
- 工具返回的 observation 就是**事实**，直接基于它回答
- ❌ 禁止用另一个工具"验证"刚拿到的 observation（如 list_dir 后不要 grep 文件是否存在）
- ❌ 禁止对不存在的文件重复搜索（列表里没有就是没有）
- ✅ list_dir 的结果 + read_file 的内容 = 完整答案，直接 done=true

[TOOL_WHITELIST_HINT]
**工具名白名单**：只能调用"可用工具"里出现过的名字。
- ❌ 禁止编造工具名（如 resolve_workspace / scan_tree / count_by_ext）
- ❌ 禁止把 count_files 拆成"子步骤"
- ✅ 不确定时直接 done=true 说明
"""


def build_system_prompt(workspace: str, max_steps: int,
                        domains: list | None = None) -> str:
    tools = "\n".join(spec.render() for spec in specs())
    base = SYSTEM_TEMPLATE.format(
        tools=tools, workspace=workspace, max_steps=max_steps,
    )
    if domains:
        allowed = ", ".join(domains)
        base += (
            "\n\n[领域约束] 用户只授权你使用以下领域的数据："
            f"{allowed}。"
            "调用 domain_search / domain_lookup / domain_term 工具时，"
            "domain 参数必须在这份清单内；"
            "其他领域一律不要调用，否则会被后端拒绝。"
        )
    return base


_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(\{[\s\S]*?\})\s*</tool_call>",
    re.IGNORECASE,
)
_CODE_BLOCK_RE = re.compile(r"```[a-zA-Z]*\s*([\s\S]*?)\s*```")


def _extract_json_candidates(text: str):
    """按 `{` 位置枚举，逐个尝试 balanced 子串。"""
    n = len(text)
    for start in range(n):
        if text[start] != "{":
            continue
        depth = 0
        in_str = False
        escape = False
        for i in range(start, n):
            ch = text[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield text[start : i + 1]
                    break


_DONE_ALIASES = frozenset({"done", "finish", "end", "complete", "完成"})


def _normalize_done(obj: dict) -> dict:
    """归一化 LLM 幻觉：把 {"action": "done", ...} 转成 {"done": True, ...}。

    工业级做法：LLM 有时把 done 当工具名用，需要无副作用归一化。
    """
    if not isinstance(obj, dict):
        return obj
    act = str(obj.get("action", "")).strip().lower()
    if act in _DONE_ALIASES and not obj.get("done"):
        obj = dict(obj)
        obj["done"] = True
        obj["answer"] = (obj.get("answer")
                         or obj.get("args", {}).get("answer")
                         or obj.get("thought", "")
                         or "(无回答)")
        obj.pop("action", None)
    # 反向：done=True 但没 answer → 用 thought 兜底
    if obj.get("done") is True and not str(obj.get("answer", "")).strip():
        obj = dict(obj)
        obj["answer"] = obj.get("thought", "") or "(无回答)"
    return obj


def parse_action(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()

    # 1) <tool_call>...</tool_call>（Qwen 训练格式，优先）
    m = _TOOL_CALL_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict):
                return _normalize_done(obj)
        except json.JSONDecodeError:
            pass

    # 2) Markdown 代码块
    m = _CODE_BLOCK_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(1).strip())
            if isinstance(obj, dict):
                return _normalize_done(obj)
        except json.JSONDecodeError:
            pass

    # 3) 整体尝试
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return _normalize_done(obj)
    except json.JSONDecodeError:
        pass

    # 4) 从后往前扫 balanced {}
    #    LLM 多段时最后一段最可能是最终决定
    candidates = list(_extract_json_candidates(text))
    for cand in reversed(candidates):
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict) and ("action" in obj or "done" in obj):
                return _normalize_done(obj)
        except json.JSONDecodeError:
            continue

    # 5) 兜底：任意 balanced JSON
    for cand in reversed(candidates):
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return _normalize_done(obj)
        except json.JSONDecodeError:
            continue

    return {
        "thought": "",
        "done": True,
        "answer": (text.strip()[:500] if text.strip() else "(无回答)"),
    }


__all__ = ["build_system_prompt", "parse_action"]
