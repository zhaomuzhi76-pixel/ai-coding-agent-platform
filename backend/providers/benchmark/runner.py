"""模型能力测试跑批编排（L1）。

职责：
    - 组合 L0 用例 + 判定器
    - 对 1 个 (provider, model) 跑全套用例
    - 聚合出 BenchmarkResult（加权总分 + rating + 分类分）

不负责：
    - 用例定义（cases 管）
    - 判定逻辑（evaluator 管）
    - provider 构造（调用方注入 chat/stream 函数）
    - 持久化（store 管）
    - 报告渲染（report 管）

工业级契约：
    - 完全依赖注入（chat_fn / stream_fn / cost_fn）
    - 单用例超时（防卡死）
    - 全批超时（防拖垮服务）
    - 出错不中断其它用例（fail-soft）
    - 命名具体化（BenchmarkResult，避免通用名）
\n\nCompat shim. See ._runner_parts."""
from __future__ import annotations
from ._runner_parts import *  # noqa
from ._runner_parts import (Any, AsyncIterator, Awaitable, BenchmarkCase, BenchmarkCaseResult, BenchmarkResult, BenchmarkRunner, Callable, ChatFn, CostFn, DEFAULT_CASE_TIMEOUT, DEFAULT_TOTAL_TIMEOUT, StreamFn, __all__, aggregate_by_category, aggregate_score, annotations, asyncio, dataclass, evaluate_case, field, list_cases, score_to_rating, time,)  # noqa
