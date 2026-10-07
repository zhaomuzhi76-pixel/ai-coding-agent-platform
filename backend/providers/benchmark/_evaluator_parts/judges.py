"""Judge functions — 从 evaluator.py 抽出。"""
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from .types import Judgment
from ._util import ev as _ev, extract_json as _extract_json


def judge_noop(text: str) -> Judgment:
    ok = bool((text or "").strip())
    return Judgment(ok, 1.0 if ok else 0.0,
                    "响应非空" if ok else "响应为空", _ev(text))


def judge_json_follow(text: str) -> Judgment:
    obj = _extract_json(text)
    if obj is None:
        return Judgment(False, 0.0, "未提取到有效 JSON 对象", _ev(text))
    has_status = "status" in obj
    has_value = "value" in obj
    if has_status and has_value:
        return Judgment(True, 1.0, "JSON 合法且含 status+value", _ev(text))
    if has_status or has_value:
        return Judgment(True, 0.6, "JSON 合法但字段不全", _ev(text))
    return Judgment(False, 0.3, "JSON 合法但缺关键字段", _ev(text))


def judge_tool_call(text: str) -> Judgment:
    obj = _extract_json(text)
    if obj is None:
        if "get_weather" in (text or "") and "北京" in (text or ""):
            return Judgment(True, 0.6, "无 JSON 但含关键词", _ev(text))
        return Judgment(False, 0.0, "未提取到工具调用 JSON", _ev(text))
    tool = str(obj.get("tool", "")).strip()
    args = obj.get("args") or {}
    city = str(args.get("city", "")).strip() if isinstance(args, dict) else ""
    if tool == "get_weather" and city:
        return Judgment(True, 1.0, "工具+参数正确", _ev(text))
    if tool == "get_weather":
        return Judgment(True, 0.6, "工具名正确但缺 city", _ev(text))
    return Judgment(False, 0.2, "工具名不对", _ev(text))


def judge_chinese(text: str) -> Judgment:
    t = text or ""
    if not t.strip():
        return Judgment(False, 0.0, "响应为空", "")
    zh = len(re.findall(r"[\u4e00-\u9fff]", t))
    en = len(re.findall(r"[A-Za-z]", t))
    total = zh + en
    if total == 0:
        return Judgment(False, 0.0, "无有效字符", _ev(t))
    ratio = zh / total
    if ratio >= 0.8:
        return Judgment(True, 1.0, f"中文占比 {ratio:.0%}", _ev(t))
    if ratio >= 0.5:
        return Judgment(True, 0.6, f"中文占比 {ratio:.0%}", _ev(t))
    return Judgment(False, ratio, f"中文占比过低 {ratio:.0%}", _ev(t))


def judge_long_context(text: str) -> Judgment:
    t = (text or "").strip()
    if "2" in t:
        return Judgment(True, 1.0, "正确提取长文本末尾问题答案", _ev(t))
    return Judgment(False, 0.0, "未正确回答 2", _ev(t))


def judge_reasoning(text: str) -> Judgment:
    t = text or ""
    if re.search(r"答案\s*[:：]\s*6", t):
        return Judgment(True, 1.0, "最终答案正确", _ev(t))
    if re.search(r"(?:等于|是|共|有)\s*6\b", t):
        return Judgment(True, 0.8, "含正确答案 6", _ev(t))
    if "6" in t:
        return Judgment(True, 0.5, "响应含数字 6（未必是答案）", _ev(t))
    return Judgment(False, 0.0, "未得出 6", _ev(t))


_JUDGES: dict[str, Callable[[str], Judgment]] = {
    "noop": judge_noop,
    "json_follow": judge_json_follow,
    "tool_call": judge_tool_call,
    "chinese": judge_chinese,
    "long_context": judge_long_context,
    "reasoning": judge_reasoning,
}
