"""文本归一化（工业级）。
职责：把 OCR 异体字 / Kangxi Radical / 全角 归一为标准简体。
不改语义、不做分词、不调 LLM。
工业级扩展：新增映射只需加 _MAP 一行。
"""
from __future__ import annotations
import re
import unicodedata
from typing import Dict

# 高频 Kangxi Radical / CJK 兼容字 → 标准简体
# 来源：OCR 常见误识别（Paddle 古籍字体）
_MAP: Dict[str, str] = {
    # Kangxi Radicals（⺠⽅⽢⽣⼤⽪等）
    "\u2f62": "甘",  # ⽢ → 甘
    "\u2f63": "生",  # ⽣ → 生
    "\u2f24": "大",  # ⼤ → 大
    "\u2f45": "方",  # ⽅ → 方
    "\u2f4a": "皮",  # ⽪ → 皮
    "\u2f3f": "白",  # ⽿ → 白  (常见)
    "\u2f3c": "目",  # ⽼ → 目
    "\u2f39": "牙",
    "\u2f36": "爪",
    "\u2f31": "犬",
    "\u2f2f": "水",
    "\u2f2d": "木",
    "\u2f2c": "月",
    "\u2f28": "日",
    "\u2f26": "文",
    "\u2f25": "攴",
    "\u2f22": "攵",
    "\u2f1e": "山",
    "\u2f1b": "屮",
    "\u2f18": "宀",
    "\u2f15": "寸",
    "\u2f10": "士",
    "\u2f0e": "土",
    "\u2f0d": "口",
    "\u2f0b": "十",
    "\u2f07": "厂",
    "\u2f03": "冖",
    "\u2f01": "丶",
    # CJK 兼容字 → 标准简体
    "\u3007": "〇",
    "\uf9fb": "灸",
    "\uf9fc": "灸",
    "\uf9fd": "灸",
    "\uf9fe": "灸",
    "\uf9ff": "灸",
    # 全角标点
    "\uff0c": ",",
    "\u3002": ".",
    "\uff1b": ";",
    "\uff1a": ":",
    "\uff08": "(",
    "\uff09": ")",
    # 常用繁体 → 简体（若数据混入繁体）
    "藥": "药",
    "湯": "汤",
    "補": "补",
    "氣": "气",
    "黃": "黄",
    "陰": "阴",
    "陽": "阳",
    "歸": "归",
    "經": "经",
    "絡": "络",
    "風": "风",
    "熱": "热",
    "濕": "湿",
    "虛": "虚",
    "實": "实",
    "傷": "伤",
    "寒": "寒",
}


def normalize(text: str) -> str:
    """归一化。不改语义、不删字符。"""
    if not text:
        return text
    # 1. NFKC：Kangxi Radical → 标准字符、全角 → 半角
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass
    # 2. 手动映射（NFKC 覆盖不到的）
    if _MAP:
        trans = str.maketrans(_MAP)
        text = text.translate(trans)
    return text


def normalize_hits(hits):
    """批量归一 hit.text（就地修改）。"""
    for h in hits or ():
        try:
            if isinstance(h, dict) and h.get("text"):
                h["text"] = normalize(str(h["text"]))
        except Exception:
            continue
    return hits


def has_simplified(text: str, keywords) -> bool:
    """检查归一化后是否含所有关键词（用简体字典）。"""
    t = normalize(text or "")
    return all(k in t for k in keywords)


__all__ = ["normalize", "normalize_hits", "has_simplified", "_MAP"]
