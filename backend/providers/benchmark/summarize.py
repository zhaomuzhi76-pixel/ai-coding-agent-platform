"""单模型能力总结 —— 基于最近一次 benchmark 结果生成一句话点评"""
from typing import Any, Dict, List

from .domains import summarize_by_domain


_CATEGORY_LABEL = {
    "latency": "响应速度",
    "stability": "稳定性",
    "capability": "综合能力",
    "cost": "性价比",
}


def _verdict(avg: float) -> str:
    if avg >= 0.9: return "表现优秀"
    if avg >= 0.7: return "表现良好"
    if avg >= 0.5: return "表现一般"
    if avg >= 0.3: return "表现较差"
    return "表现不佳"


def summarize_result(run: Dict[str, Any]) -> Dict[str, Any]:
    """输入 benchmark run dict → 输出结构化总结"""
    by_cat: Dict[str, List[float]] = {}
    for c in run.get("cases", []):
        by_cat.setdefault(c.get("category", "other"), []).append(
            float(c.get("score", 0.0))
        )

    cat_avg = {k: round(sum(v) / len(v), 4) for k, v in by_cat.items() if v}
    sorted_cats = sorted(cat_avg.items(), key=lambda x: -x[1])
    strongest = sorted_cats[0] if sorted_cats else None
    weakest = sorted_cats[-1] if sorted_cats else None

    overall = float(run.get("score", 0.0))
    if overall > 1.0:  # 兼容 100 分制
        overall /= 100.0

    # 找失败用例
    failed = [c for c in run.get("cases", []) if not c.get("passed")]

    # 一句话点评
    parts: List[str] = []
    parts.append(f"{run.get('model', '?')} 综合{_verdict(overall)}"
                 f"（{(overall * 100):.0f} 分）")
    if strongest:
        parts.append(f"{_CATEGORY_LABEL.get(strongest[0], strongest[0])}是其强项"
                     f"（{(strongest[1] * 100):.0f} 分）")
    if weakest and weakest[1] < 0.6:
        parts.append(f"{_CATEGORY_LABEL.get(weakest[0], weakest[0])}是短板"
                     f"（{(weakest[1] * 100):.0f} 分）")
    if failed:
        names = [c.get("name", c.get("case_id", "?")) for c in failed[:3]]
        parts.append(f"未通过：{'、'.join(names)}")
    else:
        parts.append("全部用例通过")

    by_domain = summarize_by_domain(run.get("cases", []))

    return {
        "model": run.get("model", ""),
        "provider": run.get("provider", ""),
        "by_domain": by_domain,
        "overall_score": round(overall, 4),
        "verdict": _verdict(overall),
        "by_category": cat_avg,
        "strongest": strongest[0] if strongest else "",
        "weakest": weakest[0] if weakest else "",
        "failed_cases": [c.get("case_id", "") for c in failed],
        "passed_count": run.get("passed_count", 0),
        "case_count": run.get("case_count", 0),
        "summary": " · ".join(parts),
    }


def compare_verdict(runs: List[Dict[str, Any]]) -> str:
    """多模型对比总结"""
    if len(runs) < 2:
        return ""
    scored = sorted(runs, key=lambda r: -float(r.get("score", 0)))
    best = scored[0]
    lines = [f"共对比 {len(runs)} 个模型："]
    lines.append(
        f"🏆 综合第一：{best.get('model')} "
        f"（{float(best.get('score', 0)) * 100:.0f} 分）"
    )
    # 每项最快
    cats = ["latency", "stability", "capability", "cost"]
    for cat in cats:
        best_cat = None
        best_score = -1
        for r in runs:
            for c in r.get("cases", []):
                if c.get("category") == cat:
                    s = float(c.get("score", 0))
                    if s > best_score:
                        best_score = s
                        best_cat = r.get("model", "")
        if best_cat:
            lines.append(
                f"{_CATEGORY_LABEL.get(cat, cat)}最佳："
                f"{best_cat}（{best_score * 100:.0f} 分）"
            )
    return " · ".join(lines)
