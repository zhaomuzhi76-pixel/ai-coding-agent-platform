"""用例 → 领域映射（能力维度）"""
from typing import Any, Dict, List

# 每个 case_id 归属的领域（可多域）
CASE_DOMAIN: Dict[str, List[str]] = {
    "first_token":     ["性能"],
    "full_latency":    ["性能"],
    "success_rate":    ["稳定性"],
    "consistency":     ["稳定性"],
    "json_follow":     ["结构化输出"],
    "tool_call":       ["工具调用"],
    "chinese":         ["中文能力"],
    "long_context":    ["长上下文"],
    "reasoning":       ["推理能力"],
    "cost_per_call":   ["成本"],
}

DOMAIN_ORDER = [
    "性能", "稳定性", "结构化输出", "工具调用",
    "中文能力", "长上下文", "推理能力", "成本",
]


def domain_of(case_id: str) -> List[str]:
    return CASE_DOMAIN.get(case_id, ["其他"])


def summarize_by_domain(cases: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """按领域聚合分数/通过率"""
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for c in cases:
        for dom in domain_of(c.get("case_id", "")):
            buckets.setdefault(dom, []).append(c)

    out: Dict[str, Dict[str, Any]] = {}
    for dom, items in buckets.items():
        scores = [float(x.get("score", 0.0)) for x in items]
        passes = [bool(x.get("passed", False)) for x in items]
        # 归一化到 0-100
        avg = sum(scores) / len(scores) if scores else 0.0
        if avg <= 1.0:
            avg *= 100
        out[dom] = {
            "domain": dom,
            "count": len(items),
            "score": round(avg, 1),
            "passed": sum(passes),
            "total": len(items),
            "cases": [x.get("case_id", "") for x in items],
        }
    return out


def domain_list() -> List[Dict[str, Any]]:
    return [{"name": d, "cases": [k for k, v in CASE_DOMAIN.items() if d in v]}
            for d in DOMAIN_ORDER]
