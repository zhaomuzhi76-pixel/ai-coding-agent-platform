"""Part 2 of runner.py."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (BenchmarkCase, BenchmarkCaseResult, Callable, ChatFn, CostFn, DEFAULT_CASE_TIMEOUT, DEFAULT_TOTAL_TIMEOUT, StreamFn, asyncio, dataclass, evaluate_case, list_cases, time,)  # noqa
from .part1 import BenchmarkResult  # noqa
from .part1 import aggregate_by_category  # noqa
from .part1 import aggregate_score  # noqa
from .part1 import score_to_rating  # noqa

@dataclass
class BenchmarkRunner:
    chat_fn: ChatFn
    stream_fn: StreamFn | None = None
    cost_fn: CostFn | None = None
    case_timeout_sec: float = DEFAULT_CASE_TIMEOUT
    total_timeout_sec: float = DEFAULT_TOTAL_TIMEOUT

    def __post_init__(self) -> None:
        if not callable(self.chat_fn):
            raise TypeError("chat_fn must be callable")
        if self.stream_fn is not None and not callable(self.stream_fn):
            raise TypeError("stream_fn must be callable or None")
        if self.cost_fn is not None and not callable(self.cost_fn):
            raise TypeError("cost_fn must be callable or None")
        if self.case_timeout_sec <= 0:
            raise ValueError("case_timeout_sec must be > 0")
        if self.total_timeout_sec <= 0:
            raise ValueError("total_timeout_sec must be > 0")

    async def run_one_case(
        self,
        case: BenchmarkCase,
        *,
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> BenchmarkCaseResult:
        """跑单个用例（含 repeats）。

        - stream 用例：走 stream_fn 测首 token
        - 其它：走 chat_fn
        - 单次超时 → 立即 break（保留已成功响应）
        """
        responses: list[str] = []
        latencies: list[float] = []
        first_token_ms = 0.0
        error = ""

        for attempt in range(case.repeats):
            if on_progress:
                try:
                    on_progress(case.case_id, attempt + 1, case.repeats)
                except Exception as e:
                    swallow("providers.benchmark._runner_parts.part2:53", e)

            t0 = time.perf_counter()
            try:
                text, first_tok = await asyncio.wait_for(
                    self._invoke_once(case),
                    timeout=self.case_timeout_sec,
                )
                lat = (time.perf_counter() - t0) * 1000.0
                latencies.append(lat)
                responses.append(text)
                if first_tok > 0 and first_token_ms == 0:
                    first_token_ms = first_tok
            except asyncio.TimeoutError:
                error = f"timeout after {self.case_timeout_sec}s"
                break
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                break

        latency_ms = max(latencies) if latencies else 0.0
        in_tok = 0
        out_tok = 0
        if responses:
            in_tok = self._estimate_input_tokens(case)
            out_tok = sum(self._estimate_tokens(r) for r in responses)
        cost = 0.0
        if self.cost_fn is not None and in_tok + out_tok > 0:
            try:
                cost = float(self.cost_fn("", in_tok, out_tok))
            except Exception:
                cost = 0.0

        return evaluate_case(
            case, responses,
            latency_ms=latency_ms,
            first_token_ms=first_token_ms,
            cost=cost,
            input_tokens=in_tok,
            output_tokens=out_tok,
            error=error,
        )

    async def run_all(
        self,
        provider: str,
        model: str,
        cases: tuple[BenchmarkCase, ...] | None = None,
        *,
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> BenchmarkResult:
        """跑全套用例（默认 10 个）。"""
        case_list = cases or list_cases()
        started = time.time()

        # 全批超时
        try:
            results = await asyncio.wait_for(
                self._run_sequence(case_list, on_progress),
                timeout=self.total_timeout_sec,
            )
            error = ""
        except asyncio.TimeoutError:
            results = []
            error = f"total timeout after {self.total_timeout_sec}s"

        finished = time.time()
        score = aggregate_score(tuple(results))
        return BenchmarkResult(
            provider=provider,
            model=model,
            started_at=started,
            finished_at=finished,
            cases=tuple(results),
            score=score,
            rating=score_to_rating(score),
            by_category=aggregate_by_category(tuple(results)),
            error=error,
        )

    # ── 内部 ──
    async def _run_sequence(
        self,
        case_list: tuple[BenchmarkCase, ...],
        on_progress: Callable[[str, int, int], None] | None,
    ) -> list[BenchmarkCaseResult]:
        out: list[BenchmarkCaseResult] = []
        for case in case_list:
            r = await self.run_one_case(case, on_progress=on_progress)
            out.append(r)
        return out

    async def _invoke_once(
        self, case: BenchmarkCase,
    ) -> tuple[str, float]:
        """调一次 provider，返回 (响应文本, 首 token ms)。

        - stream 用例：需 stream_fn
        - 非 stream：需 chat_fn
        """
        messages: list[dict] = []
        if case.system:
            messages.append({"role": "system", "content": case.system})
        messages.append({"role": "user", "content": case.prompt})

        kwargs = {
            "temperature": case.temperature,
            "max_tokens": case.max_tokens,
        }

        if case.stream:
            if self.stream_fn is None:
                raise RuntimeError("case.stream=True but stream_fn is None")
            t0 = time.perf_counter()
            first_tok_ms = 0.0
            buf: list[str] = []
            async for chunk in self.stream_fn(messages, kwargs):
                if first_tok_ms == 0.0:
                    first_tok_ms = (time.perf_counter() - t0) * 1000.0
                if chunk:
                    buf.append(str(chunk))
            return "".join(buf), first_tok_ms

        text = await self.chat_fn(messages, kwargs)
        return str(text), 0.0

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """粗糙估算：1 token ≈ 4 字符（英文）/ 1.5 字符（中文混合）。"""
        t = text or ""
        if not t:
            return 0
        # 简单：max(len/4, len/1.5) → 取中值 len/3
        return max(1, len(t) // 3)

    def _estimate_input_tokens(self, case: BenchmarkCase) -> int:
        total = (case.system or "") + case.prompt
        return self._estimate_tokens(total)
