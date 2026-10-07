"""Mixin 2 of CostTracker."""
from ._header import Any, CallRecord, Dict, List, Optional, Tuple, _agg_bucket, _finalize, _percentile, annotations, defaultdict, is_local_provider, time
from .helpers import _percentile, _agg_bucket, _finalize

class _Mixin2:
    def summary(self) -> Dict[str, Any]:
        """别名：stats()（兼容旧调用）。"""
        return self.stats()

    def history_days(self, days: int = 7) -> Dict[str, Any]:
        """最近 N 天按天统计（用于趋势图）。"""
        now = time.time()
        since = now - days * 86400
        return self.stats(since=since)

    def recent(self, limit: int = 50) -> List[CallRecord]:
        try:
            from backend.providers.cost.storage import query_records
            rows = query_records(limit=limit)
            out = [
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
            out.reverse()  # 时间正序
            return out
        except Exception:
            return self._records[-limit:]

    def price_table(self) -> Dict[str, Dict[str, float]]:
        return dict(self._price_table)

    def reset(self) -> None:
        self._records.clear()
        try:
            from backend.providers.cost.storage import reset_records
            reset_records()
        except Exception:  # silent-ok
            pass
        try:
            from backend.providers.cost.storage import reset_records
            reset_records()
        except Exception:  # silent-ok
            pass

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "records": len(self._records),
            "priced_models": list(self._price_table.keys()),
        }
