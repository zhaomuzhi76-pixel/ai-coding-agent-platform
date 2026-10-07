"""L3 提取：规则优先（快、稳）+ 可选 LLM 增强。"""
from __future__ import annotations

import re
from typing import Any

from backend.agent_learning.kinds import (
    DEFAULT_CONFIDENCE, RULES,
)

_COMPILED = tuple(
    (re.compile(pat), kind, key, mode)
    for pat, kind, key, mode in RULES
)


class RuleExtractor:
    VERSION = "1.0"

    def extract(self, text: str) -> list[dict[str, Any]]:
        """从单条用户消息提取候选偏好。"""
        if not text or not text.strip():
            return []
        out: list[dict[str, Any]] = []
        for regex, kind, key, _mode in _COMPILED:
            for m in regex.finditer(text):
                val = (m.group(1) or "").strip()
                if not val:
                    continue
                out.append({
                    "kind": kind, "key": key, "value": val,
                    "confidence": DEFAULT_CONFIDENCE,
                    "source": "rule",
                    "evidence": m.group(0)[:80],
                })
        return _dedup(out)


def _dedup(items: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict] = []
    for it in items:
        sig = (it["kind"], it["key"], it["value"])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(it)
    return out


class LlmExtractor:
    """LLM 提取（可选）：调现有 provider gateway。未就绪则返回空。"""
    VERSION = "1.0"

    PROMPT = (
        "从用户最近对话中提取长期偏好和规则参数（不是临时需求）。"
        "输出 JSON 数组。两种记录：\n"
        "1) 偏好："
        "{\"kind\":\"language|style|tech_stack|code_style|"
        "domain|workflow|dislike|other\","
        "\"key\":\"短标识\",\"value\":\"偏好值\","
        "\"confidence\":0-100}\n"
        "2) 规则参数（用户修改阈值/开关）："
        "{\"kind\":\"rule_param\","
        "\"key\":\"<rule_id>.<param>\","
        "\"value\":\"新值\",\"confidence\":0-100}\n"
        "rule_param 示例：用户说'单文件改为200行' → "
        "key=\"file_size_max_230.max_lines\", value=\"200\"；"
        "用户说'相似度阈值 0.9' → "
        "key=\"no_duplicate_responsibility.high_similarity\", "
        "value=\"0.9\"；"
        "用户说'排除 vendor' → "
        "key=\"file_size_max_230.skip_patterns\", "
        "value=\"**/vendor/**\"。\n"
        "没有偏好时返回 []。只输出 JSON。"
    )

    def extract(self, conversation: str) -> list[dict[str, Any]]:
        try:
            gateway = _resolve_gateway()
        except Exception:
            return []
        if gateway is None:
            return []
        try:
            raw = gateway.chat(
                messages=[
                    {"role": "system", "content": self.PROMPT},
                    {"role": "user", "content": conversation[:6000]},
                ],
                max_tokens=400, temperature=0.2,
            )
        except Exception:
            return []
        return _parse_json(raw)


def _resolve_gateway() -> Any:
    try:
        from backend.application.provider_gateway.gateway import (
            get_default_gateway,
        )
        return get_default_gateway()
    except Exception:
        return None


def _parse_json(raw: Any) -> list[dict]:
    import json
    if isinstance(raw, dict):
        text = raw.get("content") or raw.get("text") or ""
    else:
        text = str(raw)
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < 0:
        return []
    try:
        arr = json.loads(text[start:end + 1])
    except Exception:
        return []
    out: list[dict] = []
    for it in arr if isinstance(arr, list) else []:
        if not isinstance(it, dict):
            continue
        k = str(it.get("kind") or "other")
        key = str(it.get("key") or "")
        val = str(it.get("value") or "")
        if not key or not val:
            continue
        conf = int(it.get("confidence") or DEFAULT_CONFIDENCE)
        out.append({"kind": k, "key": key, "value": val,
                    "confidence": max(0, min(100, conf)),
                    "source": "llm", "evidence": ""})
    return out


__all__ = ["RuleExtractor", "LlmExtractor"]
