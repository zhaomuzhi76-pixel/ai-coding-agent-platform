"""模型能力测试用例（10 个维度）。

职责：
    - 定义用例规格（prompt / 期望 / 判定函数 / 权重）
    - 查询用例（list / get）
    - 注册新用例（未来扩展）

不负责：
    - 执行用例（runner 管）
    - 判定逻辑（evaluator 管）
    - 持久化（store 管）

命名：
    BenchmarkCase · 避免与 backend/quality / backend/tests 层 TestCase 冲突
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    name: str
    category: str            # latency / stability / capability / cost
    prompt: str
    system: str = ""
    expected: str = ""
    max_tokens: int = 64
    temperature: float = 0.0
    weight: float = 1.0
    repeats: int = 1
    judge: str = "noop"
    stream: bool = False
    metadata: tuple = ()

    def __post_init__(self) -> None:
        for n in ("case_id", "name", "category", "prompt"):
            v = getattr(self, n)
            if not isinstance(v, str) or not v.strip():
                raise ValueError("BenchmarkCase." + n + " required")
        if self.repeats < 1:
            raise ValueError("BenchmarkCase.repeats must be >= 1")
        if self.weight <= 0:
            raise ValueError("BenchmarkCase.weight must be > 0")
        if self.max_tokens < 1:
            raise ValueError("BenchmarkCase.max_tokens must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "category": self.category,
            "prompt": self.prompt,
            "system": self.system,
            "expected": self.expected,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "weight": self.weight,
            "repeats": self.repeats,
            "judge": self.judge,
            "stream": self.stream,
            "metadata": list(self.metadata),
        }


_FIRST_TOKEN = BenchmarkCase(
    case_id="first_token", name="首 token 延迟", category="latency",
    prompt="用一句话介绍你自己。", max_tokens=32,
    judge="noop", stream=True,
    expected="< 500ms 优秀，< 2s 合格",
)

_FULL_LATENCY = BenchmarkCase(
    case_id="full_latency", name="完整响应延迟", category="latency",
    prompt="用一句话介绍你自己。", max_tokens=32,
    judge="noop",
    expected="< 3s 优秀，< 10s 合格",
)

_SUCCESS_RATE = BenchmarkCase(
    case_id="success_rate", name="调用成功率", category="stability",
    prompt="回复 OK。", max_tokens=8, repeats=3,
    judge="noop",
    expected="100% 优秀，>=80% 合格",
)

_JSON_FOLLOW = BenchmarkCase(
    case_id="json_follow", name="JSON 遵循", category="capability",
    system="You are a JSON-only assistant. Output ONLY valid JSON, no markdown.",
    prompt='输出一个 JSON 对象，格式：{"status": "ok", "value": 42}',
    max_tokens=64, judge="json_follow",
    expected="严格 JSON，含 status 和 value 字段",
)

_TOOL_CALL = BenchmarkCase(
    case_id="tool_call", name="工具调用", category="capability",
    system=(
        "You have a tool: get_weather(city: str) -> str. "
        'To call it, output EXACTLY: {"tool": "get_weather", "args": {"city": "..."}}'
    ),
    prompt="北京今天的天气怎么样？", max_tokens=64,
    judge="tool_call",
    expected='输出 {"tool": "get_weather", "args": {"city": "北京"}}',
)

_CHINESE = BenchmarkCase(
    case_id="chinese", name="中文能力", category="capability",
    system="你必须用中文回答。",
    prompt="用一句话解释什么是人工智能。", max_tokens=128,
    judge="chinese",
    expected="纯中文回答，无英文单词（专有名词除外）",
)

_LONG_CONTEXT = BenchmarkCase(
    case_id="long_context", name="长上下文", category="capability",
    system="仔细阅读用户消息，只回答最后的问题。",
    prompt=(
        "以下是一段无关文本，请忽略：\n"
        + ("这是一些填充的句子，用于测试长上下文能力。\n" * 50)
        + "\n请回答：1+1 等于几？只回答数字。"
    ),
    max_tokens=16, judge="long_context",
    expected="回答包含 2",
)

_REASONING = BenchmarkCase(
    case_id="reasoning", name="推理能力", category="capability",
    system="请逐步推理后回答，最终答案格式：答案：X",
    prompt="小明有 5 个苹果，吃了 2 个，又买了 3 个，现在有几个？",
    max_tokens=128, judge="reasoning",
    expected="最终答案 = 6",
)

_COST = BenchmarkCase(
    case_id="cost_per_call", name="单次成本", category="cost",
    prompt="回复 OK。", max_tokens=8, judge="noop",
    expected="本地 $0 / 云端按 token 计",
)

_CONSISTENCY = BenchmarkCase(
    case_id="consistency", name="输出一致性", category="stability",
    prompt="用 5 个字回答：今天天气很好。", max_tokens=16,
    temperature=0.0, repeats=3, judge="noop",
    expected="3 次输出相似度 > 0.8",
)


_ALL_CASES: tuple[BenchmarkCase, ...] = (
    _FIRST_TOKEN, _FULL_LATENCY, _SUCCESS_RATE,
    _JSON_FOLLOW, _TOOL_CALL, _CHINESE,
    _LONG_CONTEXT, _REASONING, _COST, _CONSISTENCY,
)

_BY_ID: dict[str, BenchmarkCase] = {c.case_id: c for c in _ALL_CASES}


def list_cases() -> tuple[BenchmarkCase, ...]:
    return _ALL_CASES


def get_all_cases() -> tuple[BenchmarkCase, ...]:
    return _ALL_CASES


def get_case(case_id: str) -> BenchmarkCase:
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id required")
    c = _BY_ID.get(case_id.strip())
    if c is None:
        raise KeyError("case not found: " + case_id)
    return c


def list_by_category(category: str) -> tuple[BenchmarkCase, ...]:
    return tuple(c for c in _ALL_CASES if c.category == category)


def case_ids() -> tuple[str, ...]:
    return tuple(_BY_ID.keys())


__all__ = [
    "BenchmarkCase",
    "list_cases",
    "get_all_cases",
    "get_case",
    "list_by_category",
    "case_ids",
]
