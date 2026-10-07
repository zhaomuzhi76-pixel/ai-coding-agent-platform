"""Cost HTTP binding."""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from backend.providers.cost.registry import get_tracker


class CostBinding:
    VERSION = "2.0"
    PREFIX = "/api/cost"

    def summary(self) -> Dict[str, Any]:
        return get_tracker().summary() if hasattr(
            get_tracker(), "summary",
        ) else get_tracker().stats()

    def stats(
        self,
        since: Optional[float] = None,
        until: Optional[float] = None,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        t = get_tracker()
        if days is not None and days > 0:
            return t.history_days(days)
        return t.stats(since=since, until=until)

    def by_model(
        self,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        t = get_tracker()
        data = t.history_days(days) if days else t.stats()
        return {"models": data["by_model"]}

    def by_provider(
        self,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        t = get_tracker()
        data = t.history_days(days) if days else t.stats()
        return {"providers": data["by_provider"]}

    def recent(self, limit: int = 50) -> Dict[str, Any]:
        t = get_tracker()
        recs = t.recent(limit)
        return {
            "records": [r.to_dict() for r in recs],
            "count": len(recs),
        }

    def prices(self) -> Dict[str, Any]:
        return {"prices": get_tracker().price_table()}

    def reset(self) -> Dict[str, Any]:
        get_tracker().reset()
        return {"reset": True}

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["CostBinding"]
