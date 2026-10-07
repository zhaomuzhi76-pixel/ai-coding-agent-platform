"""历史领域 Provider。职责：历史事件 + 词条。"""
from __future__ import annotations
DOMAIN_ID = "history"
DISPLAY_NAME = "历史"
TOOLS = ("domain_lookup", "domain_search")
TERMS = {
    "秦朝": "中国第一个统一的中央集权王朝（前 221—前 207）。",
    "汉朝": "继秦之后的王朝（前 202—220），分西汉、东汉。",
    "唐朝": "中国最强盛的王朝之一（618—907），贞观之治、开元盛世。",
    "宋朝": "分北宋（960—1127）、南宋（1127—1279），经济文化繁荣。",
    "明朝": "朱元璋建立的王朝（1368—1644），郑和下西洋。",
    "清朝": "中国最后一个封建王朝（1636—1912）。",
    "科举制": "隋唐至清末通过考试选拔官员的制度。",
    "丝绸之路": "古代连接中国与中亚、欧洲的贸易路线。",
}
def lookup(term: str) -> str | None:
    return TERMS.get(term)
def search(keyword: str) -> list[str]:
    return [k for k in TERMS if keyword in k]
