"""方剂结构化解析（工业级）。
职责：把 OCR 乱码 text 解析成结构化 Formula 列表，再格式化成
      干净 markdown 供 LLM 使用。
不做校验（answer_validator 管）、不调 LLM、不写 trace。
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional

# 中文方剂名（2-15 字，以汤/丸/散/膏/丹/饮/煎 结尾）
_NAME_RE = re.compile(
    r'[\u4e00-\u9fff]{1,12}[汤丸散膏丹饮煎](?:加[\u4e00-\u9fff]{1,6})?')
# 编号+方名
_HEAD_RE = re.compile(
    r'(?:^|\n)\s*\d{4,6}\s*([\u4e00-\u9fff]{2,15}[汤丸散膏丹饮煎])')
# 【key】value
_SEC_RE = re.compile(r'【([^】]{1,6})】\s*([^【\n]*)')
# 药味清洗
_QUANT_RE = re.compile(
    r'各\s*等分|各\s*[一二三四五六七八九十百\d]+[两钱分克枚片升合匕]?'
    r'|[一二三四五六七八九十百\d]+[两钱分克枚升合]'
    r'|[（(][^）)]{1,8}[）)]')
_SEP_RE = re.compile(r'[，。；、,\.\s]+')

_KNOWN_FIELDS = ("组成", "主治", "用法", "方源", "功用", "宜忌", "加减", "备考")


@dataclass
class Formula:
    name: str
    source: str = ""
    composition: List[str] = field(default_factory=list)
    indications: str = ""
    usage: str = ""

    @property
    def valid(self) -> bool:
        return bool(self.name) and len(self.composition) > 0


def split_herbs(text: str) -> List[str]:
    """从【组成】文本切药味（每 2 字）。"""
    if not text:
        return []
    t = _QUANT_RE.sub(' ', text)
    t = _SEP_RE.sub(' ', t)
    pieces = re.findall(r'[\u4e00-\u9fff]{2}', t)
    out: List[str] = []
    for p in pieces:
        if p not in out:
            out.append(p)
    return out


def _parse_sections(seg: str) -> dict:
    out = {}
    for m in _SEC_RE.finditer(seg):
        k = m.group(1).strip()
        v = m.group(2).strip()
        if k in _KNOWN_FIELDS:
            out[k] = v
    return out


def extract_formulas(text: str) -> List[Formula]:
    """从 text 抽结构化方剂列表。
    切段策略：
      1. 用编号+方名切段（`_HEAD_RE`）
      2. 无编号的退化：按 "方名\n" 切（少见）
    """
    if not text:
        return []
    heads = list(_HEAD_RE.finditer(text))
    if not heads:
        # 退化：全文当一段，方名从 _NAME_RE 猜
        m = _NAME_RE.search(text)
        if not m:
            return []
        sec = _parse_sections(text)
        return [Formula(
            name=m.group(0),
            source=sec.get("方源", ""),
            composition=split_herbs(sec.get("组成", "")),
            indications=sec.get("主治", "")[:200],
            usage=sec.get("用法", "")[:200],
        )]

    out: List[Formula] = []
    for i, m in enumerate(heads):
        name = m.group(1).strip()
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        seg = text[start:end]
        sec = _parse_sections(seg)
        out.append(Formula(
            name=name,
            source=sec.get("方源", "")[:80],
            composition=split_herbs(sec.get("组成", "")),
            indications=sec.get("主治", "")[:200],
            usage=sec.get("用法", "")[:200],
        ))
    return out


_PRIORITY_SOURCES = [
    s.strip() for s in __import__("os").environ.get(
        "RAG_CHAT_AUTHORITATIVE_SOURCES",
        "伤寒论,金匮要略,金匮,内经,神农本草经,外台,千金").split(",")
    if s.strip()
]


def _source_priority(src: str) -> int:
    """经典方源优先级（越小越优先，非经典 100）。"""
    if not src:
        return 99
    for i, kw in enumerate(_PRIORITY_SOURCES):
        if kw in src:
            return i
    return 100


def _rank_formulas(formulas: List[Formula]) -> List[Formula]:
    """先按 source_priority 排，再按组成数降序。"""
    valid = [f for f in formulas if f.valid]
    valid.sort(key=lambda f: (_source_priority(f.source),
                              -len(f.composition)))
    return valid


def format_for_llm(formulas: List[Formula], *, limit: int = 8) -> str:
    """格式化干净 markdown 供 LLM 使用。
    只输出有效方剂（有组成），**权威方源排前**，最多 limit 个。
    """
    valid = _rank_formulas(formulas)[:limit]
    if not valid:
        return ""
    parts = []
    for i, f in enumerate(valid, 1):
        head = f"[{i}] {f.name}"
        if f.source:
            head += f"（{f.source}）"
        lines = [head]
        lines.append(f"  组成：{'、'.join(f.composition)}")
        if f.indications:
            lines.append(f"  主治：{f.indications}")
        if f.usage:
            lines.append(f"  用法：{f.usage}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


__all__ = ["Formula", "extract_formulas", "split_herbs",
           "format_for_llm", "_rank_formulas", "_source_priority"]
