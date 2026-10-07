"""中医领域 Provider。职责与 agriculture.py / finance.py 对齐：领域词与工具入口。

词表命中优先（快）；miss 时桥接 RAG QA（含图片）。
"""
from __future__ import annotations

DOMAIN_ID = "tcm"
DISPLAY_NAME = "中医"
TOOLS = ("domain_lookup", "domain_search", "domain_term")
TERMS = {
    "气虚": "元气不足，脏腑功能衰退的病理状态",
    "血瘀": "血液运行不畅，瘀滞于经脉或脏腑",
    "阴阳": "对立统一的两类属性，中医理论核心",
    "五行": "木火土金水，相生相克",
    "经络": "运行气血、联络脏腑的通道",
}


def lookup(term: str, history=None) -> dict | None:
    """[BRIDGE] 词表优先；miss 时桥接 RAG QA（支持多轮）。

    Args:
        term: 用户术语
        history: 可选。历史用户/助手消息（旧→新），透传给 rag_qa

    返回：
      {"answer": str, "citations": [...], "images": [...], "source": str}
      或 None（未收录）
    """
    # 1) 词表命中（快，无嵌入开销）
    hit = TERMS.get(term)
    if hit:
        return {"answer": hit, "citations": [], "images": [],
                "source": "vocab"}

    # 2) miss → RAG QA（含重排 + 生成 + 图片 + 多轮历史）
    try:
        from backend.rag.rag_qa import answer as rag_answer
        r = rag_answer(term, k_text=3, k_img=8, history=history)
        d = r.to_dict()
        ans = (d.get("answer") or "").strip()
        if not ans or ans.startswith("根据现有资料无法回答"):
            return None
        return {
            "answer": ans,
            "citations": d.get("citations", []),
            "images": d.get("images", []),
            "source": "rag_qa",
        }
    except Exception:
        return None


def search(keyword: str) -> list[str]:
    return [k for k in TERMS if keyword in k]
