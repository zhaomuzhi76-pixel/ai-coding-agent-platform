"""法律领域 Provider。职责：法律术语 + 词条。"""
from __future__ import annotations
DOMAIN_ID = "law"
DISPLAY_NAME = "法律"
TOOLS = ("domain_lookup", "domain_search")
TERMS = {
    "要约": "一方以订立合同为目的向对方作出的意思表示。",
    "承诺": "受要约人同意要约内容的意思表示，承诺生效时合同成立。",
    "诉讼时效": "权利人在法定期间内不行使权利即丧失请求法院保护的权利。",
    "不当得利": "无合法根据取得利益并致他人损失的法律事实。",
    "无因管理": "未受委托、无法律义务而管理他人事务的行为。",
    "善意取得": "受让人以合理价格善意受让无权处分人的财产，取得所有权。",
    "表见代理": "行为人无代理权但相对人有理由相信其有代理权的代理。",
    "缔约过失": "合同订立过程中因一方过失致对方损失应承担的责任。",
}
def lookup(term: str) -> str | None:
    return TERMS.get(term)
def search(keyword: str) -> list[str]:
    return [k for k in TERMS if keyword in k]
