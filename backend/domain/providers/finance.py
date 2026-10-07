"""Finance domain provider (bootstrap sample data)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.domain.models import DomainEntity, DomainTerm

_STOCKS: Dict[str, Dict[str, Any]] = {
    "600519": {"name": "贵州茅台", "exchange": "SSE",
               "industry": "白酒", "market_cap_bn": 2100.0},
    "000001": {"name": "平安银行", "exchange": "SZSE",
               "industry": "银行", "market_cap_bn": 220.0},
    "AAPL": {"name": "Apple Inc.", "exchange": "NASDAQ",
             "industry": "Technology", "market_cap_bn": 3200.0},
}

_FUNDS: Dict[str, Dict[str, Any]] = {
    "110011": {"name": "易方达中小盘", "type": "混合型", "risk": "R4"},
    "000001": {"name": "华夏成长", "type": "混合型", "risk": "R3"},
}

_TERMS: Dict[str, str] = {
    "市盈率": "市值与净利润之比，反映估值水平。",
    "夏普比率": "单位风险超额收益，衡量风险调整后表现。",
}


class FinanceProvider:
    name = "finance"

    def list_entity_types(self) -> List[str]:
        return ["stock", "fund"]

    def _table(self, entity_type: str) -> Dict[str, Dict[str, Any]]:
        if entity_type == "stock":
            return _STOCKS
        if entity_type == "fund":
            return _FUNDS
        raise ValueError(f"unknown entity_type: {entity_type}")

    def list_entities(self, entity_type: str) -> List[str]:
        return sorted(self._table(entity_type).keys())

    def lookup_entity(
        self, entity_type: str, name: str,
    ) -> Optional[DomainEntity]:
        table = self._table(entity_type)
        key = (name or "").strip()
        if not key:
            return None
        if key in table:
            return DomainEntity(entity_type, key, dict(table[key]))
        for k, attrs in table.items():
            if key == attrs.get("name") or key in k or k in key:
                return DomainEntity(entity_type, k, dict(attrs))
        return None

    def search_entities(
        self, query: str, limit: int = 10,
    ) -> List[DomainEntity]:
        q = (query or "").strip().lower()
        if not q:
            return []
        out: List[DomainEntity] = []
        for et, table in (("stock", _STOCKS), ("fund", _FUNDS)):
            for code, attrs in table.items():
                hay = f"{code} {' '.join(str(v) for v in attrs.values())}".lower()
                if q in hay:
                    out.append(DomainEntity(et, code, dict(attrs)))
                    if len(out) >= limit:
                        return out
        return out

    def lookup_term(self, name: str) -> Optional[DomainTerm]:
        key = (name or "").strip()
        if key in _TERMS:
            return DomainTerm(term_type="glossary", name=key,
                              definition=_TERMS[key])
        return None

    def list_terms(self) -> List[str]:
        return sorted(_TERMS.keys())

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict:
        return {
            "name": self.name,
            "ready": self.ready(),
            "entity_types": self.list_entity_types(),
            "entities": sum(len(self._table(t)) for t in self.list_entity_types()),
            "terms": len(_TERMS),
        }
