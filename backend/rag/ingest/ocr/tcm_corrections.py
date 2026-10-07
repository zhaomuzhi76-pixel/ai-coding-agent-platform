"""中医术语 OCR 纠错。职责：古籍/繁体 OCR 常见错误→正确术语。
保守策略：只替换明确错误串，不碰歧义词。环境变量 RAG_OCR_CORRECT=0 可关闭。
"""
from __future__ import annotations
import os
import re
from typing import List

# 长短语优先（最安全）
_PHRASES = [
    ("人民興上生廣出版社", "人民衛生出版社"),
    ("人民上生出版社", "人民衛生出版社"),
    ("金廣要略", "金匱要略"),
    ("金匱要略淺述", "金匱要略淺述"),
    ("傷寒卒病論", "傷寒卒病論"),
    ("傷寒雜病論", "傷寒雜病論"),
    ("潭日典", "譚日強"),
    ("衍寒桅", "傷寒論"),
]

# 双字纠正
_CHARS = [
    ("中匡", "中醫"),
    ("中E", "中醫"),
    ("仿寒", "傷寒"),
    ("衍寒", "傷寒"),
    ("辦延", "辨證"),
    ("辦證", "辨證"),
    ("辨延", "辨證"),
    ("脈延", "脈證"),
    ("爽飲", "咳嗽"),
    ("士匕", "吐"),
    ("大車", "大棗"),
    ("慧蘇", "蘇子"),
    ("痙濕喝", "痙濕暍"),
    ("中風曆節", "中風歷節"),
    ("肺癱", "肺癰"),
]

# 单字正则（仅高危字）
_REGEX = [
    (re.compile(r'桅'), '論'),
]

_P = [(re.compile(re.escape(b)), g) for b, g in _PHRASES]
_C = [(re.compile(re.escape(b)), g) for b, g in _CHARS]


def is_enabled() -> bool:
    return os.environ.get("RAG_OCR_CORRECT", "1") == "1"


def correct(text: str) -> str:
    if not text or not is_enabled():
        return text
    for pat, good in _P:
        text = pat.sub(good, text)
    for pat, good in _C:
        text = pat.sub(good, text)
    for pat, good in _REGEX:
        text = pat.sub(good, text)
    return text


def correct_many(texts: List[str]) -> List[str]:
    return [correct(t) for t in texts]


__all__ = ["correct", "correct_many", "is_enabled"]
