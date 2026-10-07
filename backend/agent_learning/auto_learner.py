"""从用户消息自动学习（含 scope + LLM 语义）。"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import re
from typing import Any

from backend.agent_learning import profile_ops
from backend.agent_learning.scope import RuleScope, detect_scope


_RULES: tuple[tuple[str, str, str], ...] = (
    ("code_style", "forbid",
     r"(?:禁止|不要|别|不允许|禁用)\s*(?:用|使用)?\s*"
     r"([A-Za-z_][A-Za-z0-9_.]{1,40})"),
    ("code_style", "require",
     r"(?:必须|一定要|务必|都要|一律|统一)\s*(?:用|使用)?\s*"
     r"([A-Za-z_][A-Za-z0-9_.]{1,40})"),
    ("code_style", "max_lines",
     r"(?:最多|不超过|不能超过|不能多于)\s*(\d{2,4})\s*(?:行|line)"),
    ("code_style", "naming",
     r"(?:命名|变量名|函数名)\s*(?:用|要|必须|一律)?\s*"
     r"(snake_case|camelCase|PascalCase)"),
    ("workflow", "python_version",
     r"(?:Python|python)\s*(3\.\d{1,2})"),
    ("tech_stack", "framework",
     r"(?:框架|用)\s*(FastAPI|Django|Flask|React|Vue|"
     r"Next\.js|Vite|Tailwind)"),
    ("workflow", "error_handling",
     r"(?:错误处理|异常处理)\s*(?:要|必须|一律|统一)\s*"
     r"([^\s，。,.!?]{2,30})"),
)

# 规则参数识别（正则，无需 LLM）：用户说"改为 N" → rule_param
_PARAM_RULES: tuple[tuple[str, str, str], ...] = (
    # 行数：多种说法（单文件/每个文件/文件/上限 + 改为/不超过 + N 行）
    (r"(?:单文件|每个文件|文件|行数|上限|最多|不超过|不能超过|改为|改成)"
     r"[^\d]{0,15}?(\d{2,4})\s*行",
     "file_size_max_230", "max_lines"),
    # 相似度阈值：宽容中间词（阈值/值/分/改为/...）
    (r"(?:相似度|相似|阈值)[^\d]{0,20}?(0?\.\d+)",
     "no_duplicate_responsibility", "high_similarity"),
    # 通用：<rule_id>.<param> = <value>
    (r"([a-z_][a-z0-9_]{2,40})\s*(?:的|\.)\s*"
     r"([a-z_][a-z0-9_]{1,40})\s*"
     r"(?:改|调整|设|为|到|=|上限)\s*[:=]?\s*([\w.]+)",
     None, None),
)
# 从 _PARAM_RULES 提取参数 key（如 max_lines / high_similarity）
# 用于 _COMPILED 循环去重（参数类由 rule_param 统一处理）
_PARAM_KEYS = frozenset(
    param for _, _, param in _PARAM_RULES if param is not None
)


_PARAM_COMPILED = tuple(
    (re.compile(pat), rid, param)
    for pat, rid, param in _PARAM_RULES
)


_COMPILED = tuple((k, key, re.compile(pat)) for k, key, pat in _RULES)
_NOISE = frozenset({"它", "这个", "那个", "什么", "怎么", "为什么",
                    "用", "使用", "代码", "函数", "文件"})


class AutoLearner:
    VERSION = "2.0"

    def __init__(self, *, min_conf: int = 95, use_llm: bool = False) -> None:
        self.min_conf = min_conf
        self.use_llm = use_llm
        self.last_learned: list[dict[str, Any]] = []

    def learn_from_message(
        self, message: str, *, workspace: str = "",
    ) -> list[dict[str, Any]]:
        if not message or not message.strip():
            return []
        scope = detect_scope(message, workspace=workspace)
        learned: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for kind, key, regex in _COMPILED:
            # _COMPILED 循环去重：参数类 key（max_lines/...）交给 rule_param
            if key in _PARAM_KEYS:
                continue
            for m in regex.finditer(message):
                val = (m.group(1) or "").strip()
                if not val or val in _NOISE:
                    continue
                sig = (kind, key, val)
                if sig in seen:
                    continue
                seen.add(sig)
                self._store(kind, key, val, scope, workspace)
                learned.append({"kind": kind, "key": key, "value": val,
                                "scope": scope.value, "source": "auto"})

        try:
            from backend.agent_learning.extractor import RuleExtractor
            for c in RuleExtractor().extract(message):
                # 去重：参数类签名（如 max_lines）已由 rule_param 覆盖，不再重复存储
                if c.get("kind") == "code_style" and c.get("key") in (
                    "max_lines", "max_lines_per_file",
                    "high_similarity", "low_similarity",
                ):
                    continue
                sig = (c["kind"], c["key"], c["value"])
                if sig in seen:
                    continue
                seen.add(sig)
                self._store(c["kind"], c["key"], c["value"], scope, workspace)
                learned.append({**c, "scope": scope.value, "source": "auto"})
        except Exception as e:
            swallow("agent_learning.auto_learner:116", e)

        # ── 规则参数识别（正则，优先于 LLM） ──
        for regex, rid, param in _PARAM_COMPILED:
            for m in regex.finditer(message):
                groups = [g for g in m.groups() if g]
                if not groups:
                    continue
                if rid is None:
                    # 通用：<rule_id>.<param>=<value>
                    if len(groups) < 3:
                        continue
                    rid_v, param_v, val_v = groups[0], groups[1], groups[2]
                else:
                    rid_v = rid
                    param_v = param
                    val_v = groups[-1]
                key = f"{rid_v}.{param_v}"
                sig = ("rule_param", key, str(val_v))
                if sig in seen:
                    continue
                seen.add(sig)
                self._store("rule_param", key, str(val_v),
                            scope, workspace)
                learned.append({
                    "kind": "rule_param", "key": key,
                    "value": str(val_v),
                    "scope": scope.value, "source": "auto",
                })

        if self.use_llm:
            try:
                from backend.agent_learning.extractor import LlmExtractor
                for c in LlmExtractor().extract(message):
                    sig = (c["kind"], c["key"], c["value"])
                    if sig in seen:
                        continue
                    seen.add(sig)
                    self._store(c["kind"], c["key"], c["value"],
                                scope, workspace,
                                confidence=c.get("confidence", 80))
                    learned.append({**c, "scope": scope.value, "source": "llm"})
            except Exception as e:
                swallow("agent_learning.auto_learner:159", e)

        self.last_learned = learned
        return learned

    def _store(self, kind, key, value, scope, workspace, confidence=None):
        try:
            profile_ops.upsert(
                kind=kind, key=key, value=value,
                confidence=confidence or self.min_conf,
                scope=scope.value, workspace=workspace)
        except Exception as e:
            swallow("agent_learning.auto_learner:171", e)


_default: AutoLearner | None = None


def get_default() -> AutoLearner:
    global _default
    if _default is None:
        _default = AutoLearner(use_llm=True)
    return _default


__all__ = ["AutoLearner", "get_default"]
