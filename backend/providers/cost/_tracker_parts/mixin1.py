"""Mixin 1 of CostTracker."""
from ._header import Any, CallRecord, Dict, List, Optional, Tuple, _agg_bucket, _finalize, _percentile, annotations, defaultdict, is_local_provider, time
from backend.core.observability.silent import swallow

from .helpers import _percentile, _agg_bucket, _finalize

class _Mixin1:
    def __init__(self) -> None:
        self._records: List[CallRecord] = []
        self._price_table: Dict[str, Dict[str, float]] = {}
        self._load_prices()

    def _load_prices(self) -> None:
        try:
            from backend.providers.config import load_llm_config
            cfg = load_llm_config()
            for p in cfg.providers:
                for m in p.models:
                    self._price_table[m.id] = {
                        "in": m.cost_input_per_1k,
                        "out": m.cost_output_per_1k,
                    }
        except Exception as e:
            swallow("providers.cost._tracker_parts.mixin1:24", e)

    def price_of(self, model: str) -> Dict[str, float]:
        return self._price_table.get(model, {"in": 0.0, "out": 0.0})

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int,
    ) -> float:
        p = self.price_of(model)
        return (
            input_tokens / 1000.0 * p["in"]
            + output_tokens / 1000.0 * p["out"]
        )

    def record(
        self,
        *,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        role: str = "",
        success: bool = True,
        error: str = "",
    ) -> CallRecord:
        # 本地 provider 不计成本
        if is_local_provider(provider):
            cost = 0.0
        elif not success:
            cost = 0.0
        else:
            cost = self.calculate_cost(
                model, input_tokens, output_tokens,
            )
        rec = CallRecord(
            provider=provider, model=model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=cost, latency_ms=float(latency_ms),
            role=role, success=success, error=error,
        )
        self._records.append(rec)
        if len(self._records) > self.MAX_RECORDS:
            self._records = self._records[-self.MAX_RECORDS:]
        # 跨进程持久化
        try:
            from backend.providers.cost.storage import insert_record
            insert_record(rec.to_dict())
        except Exception as e:
            swallow("providers.cost._tracker_parts.mixin1:74", e)
        return rec

    def filter_range(
        self,
        since: Optional[float] = None,
        until: Optional[float] = None,
    ) -> List[CallRecord]:
        # 优先从 storage 读（跨进程共享）
        try:
            from backend.providers.cost.storage import query_records
            rows = query_records(since=since, until=until)
            return [
                CallRecord(
                    provider=r["provider"], model=r["model"],
                    input_tokens=r["input_tokens"],
                    output_tokens=r["output_tokens"],
                    cost=r["cost"], latency_ms=r["latency_ms"],
                    role=r["role"], success=r["success"],
                    error=r["error"],
                    record_id=r["record_id"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        except Exception:
            # 回退内存
            out = self._records
            if since is not None:
                out = [r for r in out if r.created_at >= since]
            if until is not None:
                out = [r for r in out if r.created_at <= until]
            return out

    def stats(
        self,
        since: Optional[float] = None,
        until: Optional[float] = None,
    ) -> Dict[str, Any]:
        records = self.filter_range(since, until)
        by_model: Dict[str, Dict[str, Any]] = defaultdict(_agg_bucket)
        by_provider: Dict[str, Dict[str, Any]] = defaultdict(_agg_bucket)
        by_role: Dict[str, Dict[str, Any]] = defaultdict(_agg_bucket)
        by_day: Dict[str, Dict[str, Any]] = defaultdict(_agg_bucket)

        total = _agg_bucket()
        online = _agg_bucket()
        local = _agg_bucket()
        online_providers: set = set()
        local_providers: set = set()

        for r in records:
            lat = r.latency_ms
            for bucket in (
                total,
                by_model[r.model],
                by_provider[r.provider],
                by_role[r.role or "unknown"],
                by_day[r.day_key],
            ):
                bucket["calls"] += 1
                if r.success:
                    bucket["success"] += 1
                else:
                    bucket["errors"] += 1
                bucket["input_tokens"] += r.input_tokens
                bucket["output_tokens"] += r.output_tokens
                bucket["cost"] += r.cost
                bucket["_latencies"].append(lat)

            if r.is_local:
                local["calls"] += 1
                local["cost"] += 0.0
                local["_latencies"].append(lat)
                if r.success:
                    local["success"] += 1
                else:
                    local["errors"] += 1
                local_providers.add(r.provider)
            else:
                online["calls"] += 1
                online["cost"] += r.cost
                online["input_tokens"] += r.input_tokens
                online["output_tokens"] += r.output_tokens
                online["_latencies"].append(lat)
                if r.success:
                    online["success"] += 1
                else:
                    online["errors"] += 1
                online_providers.add(r.provider)

        def finalize_map(m: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
            return {k: _finalize(v) for k, v in m.items()}

        # by_model 附 provider 信息
        model_to_provider: Dict[str, str] = {}
        for r in records:
            model_to_provider.setdefault(r.model, r.provider)
        by_model_out = finalize_map(by_model)
        for model, bucket in by_model_out.items():
            bucket["provider"] = model_to_provider.get(model, "")
            bucket["is_local"] = is_local_provider(bucket["provider"])

        return {
            "total": _finalize(total),
            "online": {**_finalize(online),
                       "providers": sorted(online_providers)},
            "local": {**_finalize(local),
                      "providers": sorted(local_providers)},
            "by_model": by_model_out,
            "by_provider": finalize_map(by_provider),
            "by_role": finalize_map(by_role),
            "by_day": dict(sorted(finalize_map(by_day).items())),
            "record_count": len(records),
        }
