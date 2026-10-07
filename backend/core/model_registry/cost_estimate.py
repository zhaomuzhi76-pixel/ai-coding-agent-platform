"""成本预估：基于 5 个角色配置估算跑一次典型任务的成本"""
from typing import Any, Dict

from backend.monitor.pricing import get_pricing  # noqa

CALL_COUNT = {"intent": 1, "plan": 1, "code": 3, "review": 1, "complex": 1}
TOKENS = {
    "intent": (500, 100), "plan": (2000, 300),
    "code": (3000, 2000), "review": (4000, 300),
    "complex": (3000, 1000),
}


def estimate(reg) -> Dict[str, Any]:
    roles_out = []
    total = 0.0
    for role, route in reg.roles.items():
        m = reg.models.get(route.primary)
        if not m:
            continue
        price = get_pricing(m.id, m.provider_id)
        calls = CALL_COUNT.get(role, 1)
        pin, pout = TOKENS.get(role, (1000, 500))
        cost = calls * (pin / 1000 * price["input"]
                        + pout / 1000 * price["output"])
        total += cost
        roles_out.append({
            "role": role, "model": m.id, "provider": m.provider_id,
            "calls": calls,
            "input_tokens": pin * calls, "output_tokens": pout * calls,
            "cost_usd": round(cost, 6),
            "is_local": m.provider_id in ("ollama-local", "local"),
        })
    return {"total_usd": round(total, 6), "roles": roles_out,
            "assumption": {"call_count": CALL_COUNT, "tokens_per_call": TOKENS}}
