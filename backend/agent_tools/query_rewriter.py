"""多轮查询重写（工业级插件）。

职责：把「它/他/她/此方/上方/该方」等指代词，用会话历史里
     最近一次出现的实体（方剂名/术语）替换，形成独立可检索 query。
不做：不调 LLM、不改语义、不扩写、不做同义替换。

设计：
- 纯函数，无状态，可单测
- 无历史 → 原样返回（零开销）
- 只替换已知代词的 *开头*，避免误伤
- 工业级扩展：新增代词/实体类型只需加 _PRONOUNS / _ENTITIES 一行
"""
from __future__ import annotations
import re
from typing import Iterable, List, Optional, Sequence

# 常见指代开头（按长度降序，避免短词先匹配）
_PRONOUNS: Sequence[str] = (
    "该方", "此方", "上方", "这个方", "那个方",
    "它", "他", "她", "此", "该",
)

# [CONT] 续问前缀（无代词但语义承接上文）
_CONTINUATIONS: Sequence[str] = (
    "还有", "还", "再", "另", "其他", "别的",
    "继续", "接着", "那么", "然后",
)

# [HERB_VOCAB] 药名词表（从 CHM-100 加载，用于无后缀药名匹配）
_HERB_VOCAB = None

def _load_herb_vocab():
    """懒加载药名词表（CHM-100 + TCMP-300 + 本草纲目 + 常用药）。"""
    global _HERB_VOCAB
    if _HERB_VOCAB is not None:
        return _HERB_VOCAB
    import json, os
    names = set()
    base = os.path.expanduser("~/xiangmu02/biancheng_aiagentpro")

    # 1) CHM-100（dict: {"1": {"name": "..."}}）
    for p in [os.path.join(base, "data/eval/chm_classes.json"),
              "data/eval/chm_classes.json"]:
        if os.path.isfile(p):
            try:
                d = json.load(open(p, encoding="utf-8"))
                for v in d.values():
                    n = str(v.get("name") or "").strip()
                    if n:
                        names.add(n)
                break
            except Exception:
                pass

    # 2) [TCMP_VOCAB] TCMP-300（dict: {"1": {"class_name": "..."}}）
    for p in [os.path.join(base, "data/eval/tcmp_classes.json"),
              "data/eval/tcmp_classes.json"]:
        if os.path.isfile(p):
            try:
                d = json.load(open(p, encoding="utf-8"))
                for v in d.values():
                    n = str(v.get("class_name") or v.get("name") or "").strip()
                    if n:
                        names.add(n)
                break
            except Exception:
                pass
    # 2) 常用药（兜底）
    names |= {
        "人参", "甘草", "当归", "黄芪", "白术", "茯苓", "陈皮",
        "生地", "熟地", "地黄", "川芎", "白芍", "赤芍", "半夏",
        "枸杞", "山药", "丹参", "三七", "附子", "干姜", "肉桂",
        "麻黄", "桂枝", "黄连", "黄芩", "黄柏", "柴胡", "葛根",
    }
    _HERB_VOCAB = names
    return names


def _find_herb_in_text(text: str):
    """从文本里找最近出现的药名（最长匹配优先）。返回 str 或 None。"""
    t = (text or "").strip()
    if not t:
        return None
    vocab = _load_herb_vocab()
    hits = [n for n in vocab if n and n in t]
    if not hits:
        return None
    # 取最长匹配
    hits.sort(key=len, reverse=True)
    return hits[0]


# 会话历史里要追踪的实体类型（方剂/术语/病名）
# 中药方剂名多为 2-5 字 + 汤/散/丸/饮/煎
_ENTITY_RE = re.compile(
    r"([\u4e00-\u9fa5]{1,6}(?:汤|散|丸|饮|煎|膏|丹))"
)


def extract_last_entity(history: Iterable[str]) -> Optional[str]:
    """从历史（旧→新）中取 *最近* 一次实体名。

    [HERB_FIRST] 优先方剂名（带后缀）；miss 时用药名词表匹配。
    """
    if not history:
        return None
    hist_list = list(history)
    for text in reversed(hist_list):
        if not text:
            continue
        # 1) 方剂名（带后缀）
        ms = _ENTITY_RE.findall(str(text))
        if ms:
            return max(ms, key=len)
    # 2) 全历史里找药名（无后缀，如"麻黄"）
    for text in reversed(hist_list):
        if not text:
            continue
        herb = _find_herb_in_text(str(text))
        if herb:
            return herb
    return None


def rewrite(query: str, history: Optional[Iterable[str]] = None) -> str:
    """把指代词替换为历史里最近一次方剂名。

    Args:
        query: 当前用户输入
        history: 旧→新 的用户/助手文本序列（不含当前 query）

    Returns:
        重写后的 query；无历史或无指代时原样返回。
    """
    q = (query or "").strip()
    if not q or not history:
        return q

    # 已经含实体 → 不重写
    if _ENTITY_RE.search(q):
        return q

    last = extract_last_entity(history)
    if not last:
        return q

    for p in _PRONOUNS:
        if q.startswith(p):
            rest = q[len(p):].lstrip("，,、 ")
            return f"{last}{rest}" if rest else last

    # [CONT] 续问前缀（"还有什么作用？" → "麻黄还有什么作用？"）
    for p in _CONTINUATIONS:
        if q.startswith(p):
            return f"{last}{q}"   # 保留原句，前置实体
    return q


def rewrite_with_debug(query: str, history=None):
    """返回 (rewritten, meta)。meta 里记录是否命中。"""
    out = rewrite(query, history)
    return out, {
        "rewritten": out != (query or "").strip(),
        "original": (query or "").strip(),
        "entity": extract_last_entity(history or []),
    }


__all__ = ["rewrite", "rewrite_with_debug", "extract_last_entity"]
