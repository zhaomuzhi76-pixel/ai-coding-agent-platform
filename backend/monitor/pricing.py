"""模型定价表（每 1k tokens，USD）—— 用户可覆盖"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

STORE = Path(os.environ.get(
    "BIANCHENG_PRICING",
    str(Path.home() / ".biancheng" / "model_pricing.json"),
))

# 默认价格表（USD / 1k tokens），用户可覆盖
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    # 阿里云百炼
    "qwen-max":        {"input": 0.0028, "output": 0.0084},
    "qwen-plus":       {"input": 0.0004, "output": 0.0012},
    "qwen-coder-plus": {"input": 0.0005, "output": 0.0015},
    # OpenAI
    "gpt-4o":          {"input": 0.0025, "output": 0.0100},
    "gpt-4o-mini":     {"input": 0.00015, "output": 0.0006},
    # Anthropic
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku":  {"input": 0.0008, "output": 0.004},
    # DeepSeek
    "deepseek-chat":    {"input": 0.00014, "output": 0.00028},
    # 智谱
    "glm-4-plus":       {"input": 0.0007, "output": 0.0007},
    # 本地（免费）
    "__local__":        {"input": 0.0, "output": 0.0},
}


def _load() -> Dict[str, Dict[str, float]]:
    if not STORE.exists():
        return {}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: Dict[str, Dict[str, float]]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(STORE.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STORE)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _match(model: str) -> Optional[Dict[str, float]]:
    """精确匹配优先，其次前缀匹配（qwen-max-2024 → qwen-max）"""
    overrides = _load()
    if model in overrides:
        return overrides[model]
    if model in DEFAULT_PRICING:
        return DEFAULT_PRICING[model]
    for k, v in {**DEFAULT_PRICING, **overrides}.items():
        if model.startswith(k):
            return v
    return None


def get_pricing(model: str, provider: str = "") -> Dict[str, float]:
    """返回 {input, output}，本地模型返回 0"""
    if provider and provider in ("ollama-local", "local", "vllm", "lmstudio"):
        return {"input": 0.0, "output": 0.0}
    if "127.0.0.1" in provider or "localhost" in provider:
        return {"input": 0.0, "output": 0.0}
    p = _match(model)
    return p if p else {"input": 0.0, "output": 0.0}


def calc_cost(model: str, provider: str,
              prompt_tokens: int, completion_tokens: int) -> float:
    p = get_pricing(model, provider)
    return round(
        (prompt_tokens / 1000.0) * p["input"]
        + (completion_tokens / 1000.0) * p["output"],
        6,
    )


def set_pricing(model: str, input_price: float, output_price: float) -> None:
    data = _load()
    data[model] = {"input": float(input_price), "output": float(output_price)}
    _save(data)


def list_pricing() -> List[Dict[str, Any]]:
    merged = {**DEFAULT_PRICING, **_load()}
    return [{"model": k, "input": v["input"], "output": v["output"]}
            for k, v in sorted(merged.items())]
