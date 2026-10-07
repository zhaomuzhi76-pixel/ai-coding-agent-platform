"""医疗领域 Provider。职责：医学名词 + 词条。不做诊断建议。"""
from __future__ import annotations
DOMAIN_ID = "medicine"
DISPLAY_NAME = "医疗"
TOOLS = ("domain_lookup", "domain_search")
TERMS = {
    "血压": "血液对血管壁的侧压力，成人正常 90-120 mmHg。",
    "血糖": "血液中的葡萄糖浓度，空腹正常 3.9-6.1 mmol/L。",
    "BMI": "身体质量指数，体重(kg)/身高(m)²，18.5-23.9 为正常。",
    "心率": "心脏每分钟跳动次数，成人静息 60-100 次/分。",
    "体温": "人体核心温度，腋下正常 36.0-37.2 ℃。",
    "抗生素": "由微生物产生或人工合成的、能抑制或杀灭细菌的药物。",
    "疫苗": "用病原微生物制成的、能诱导机体产生免疫保护的产品。",
    "糖尿病": "以慢性高血糖为特征的代谢性疾病，分 1 型和 2 型。",
}
def lookup(term: str) -> str | None:
    return TERMS.get(term)
def search(keyword: str) -> list[str]:
    return [k for k in TERMS if keyword in k]
