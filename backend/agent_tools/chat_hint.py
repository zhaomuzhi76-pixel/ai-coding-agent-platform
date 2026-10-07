"""对话提示构造（工业级）。
职责：从 Evidence 构造 hint / 从历史改写 query。
不检索（chat_evidence 管）、不校验（answer_validator 管）。
"""
from __future__ import annotations
import os
import re
from typing import List, Optional

_CLASSIC_HINT = os.environ.get("RAG_CHAT_CLASSIC_HINT", "伤寒论 金匮")
_HINT_ENABLED = os.environ.get("RAG_CHAT_HINT_ENABLED", "1") == "1"

_PRON = ("它", "他", "她", "这", "那", "其", "该", "此")
_FORMULA_RE = re.compile(r'[汤丸散膏丹]|组成|主治|配方|药味')


def needs_classic_hint(q: str) -> bool:
    if not q or len(q) > 50:
        return False
    return bool(_FORMULA_RE.search(q))


def rewrite_query(current: str, history_texts=None) -> str:
    """[ENT_FIRST] 优先用 query_rewriter 做实体替换。

    正确行为：
      "它治什么病？"  + history=["麻黄...",...]  →  "麻黄治什么病？"
      "此方主治"      + history=["桂枝汤...",...] →  "桂枝汤主治"

    回退：无实体命中时走原拼接逻辑（保持兼容）。
    """
    q = (current or "").strip()
    if not q:
        return q

    # 1) 优先：真正指代消解（实体替换）
    if history_texts:
        try:
            from backend.agent_tools.query_rewriter import rewrite as _ent
            q_ent = _ent(q, history_texts)
            if q_ent and q_ent != q:
                return q_ent
        except Exception:
            pass

    # 2) 回退：原拼接逻辑（保留向后兼容）
    need_pron = len(q) < 8 or any(p in q for p in _PRON)
    if history_texts and need_pron:
        for h in reversed(list(history_texts)):
            h = (h or "").strip()
            if h and h != q and len(h) <= 200:
                q2 = f"{h} {q}"
                if _HINT_ENABLED and needs_classic_hint(q2):
                    q2 = q2 + " " + _CLASSIC_HINT
                return q2
    if _HINT_ENABLED and needs_classic_hint(q):
        q = q + " " + _CLASSIC_HINT
    return q

def build_hint(ev: Any) -> str:
    """Evidence → 注入 hint（结构化证据 + 回答规则）。"""
    if ev is None or not getattr(ev, "ok", False):
        return ""
    clean_ctx = ""
    try:
        from backend.agent_tools.formula_parser import (
            extract_formulas, format_for_llm)
        all_f = []
        for h in (ev.hits or ()):
            text = str(h.get("text") or "")
            if text:
                all_f.extend(extract_formulas(text))
        clean_ctx = format_for_llm(all_f, limit=8)
    except Exception:
        clean_ctx = getattr(ev, "context_text", "") or ""
    if not clean_ctx:
        clean_ctx = getattr(ev, "context_text", "") or ""

    rules = "\n".join([
        "\n\n【系统已自动检索知识库，以下为结构化证据。】",
        "【回答规则】",
        "1. 严格从下方 [组成/主治/用法] 字段提取，**不得遗漏药味**。",
        "2. **不要反复调用工具**；证据已足够时直接回答。",
        "3. 证据完全没有相关信息才回答：暂无法回答",
        "",
        "【证据】",
    ])
    return rules + "\n" + clean_ctx


__all__ = ["rewrite_query", "build_hint", "needs_classic_hint"]
