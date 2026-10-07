"""Agriculture domain provider (bootstrap sample data)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.domain.models import DomainEntity, DomainTerm

_CROPS: Dict[str, Dict[str, Any]] = {
    "小麦": {"latin": "Triticum aestivum", "growing_period_days": 240,
             "optimal_temp_c": [15, 25], "soil_ph": [6.0, 7.5],
             "common_pests": ["蚜虫", "红蜘蛛"],
             "common_diseases": ["白粉病", "赤霉病"]},
    "玉米": {"latin": "Zea mays", "growing_period_days": 120,
             "optimal_temp_c": [22, 30], "soil_ph": [5.5, 7.5],
             "common_pests": ["玉米螟", "黏虫"],
             "common_diseases": ["大斑病", "小斑病"]},
    "水稻": {"latin": "Oryza sativa", "growing_period_days": 130,
             "optimal_temp_c": [25, 32], "soil_ph": [5.5, 6.5],
             "common_pests": ["稻飞虱", "二化螟"],
             "common_diseases": ["稻瘟病", "纹枯病"]},
}

_PESTICIDES: Dict[str, Dict[str, Any]] = {
    "吡虫啉": {"category": "杀虫剂", "active_ingredient": "imidacloprid",
               "target_pests": ["蚜虫", "稻飞虱"], "dosage": "10-20 g/亩",
               "pre_harvest_interval_days": 14},
    "三环唑": {"category": "杀菌剂", "active_ingredient": "tricyclazole",
               "target_diseases": ["稻瘟病"], "dosage": "20-30 g/亩",
               "pre_harvest_interval_days": 21},
}

_TERMS: Dict[str, str] = {
    "分蘖期": "禾谷类作物从基部节位长出分枝的时期。",
    "拔节期": "茎节快速伸长的时期，需水需肥高峰。",
}


class AgricultureProvider:
    name = "agriculture"

    def list_entity_types(self) -> List[str]:
        return ["crop", "pesticide"]

    def _table(self, entity_type: str) -> Dict[str, Dict[str, Any]]:
        if entity_type == "crop":
            return _CROPS
        if entity_type == "pesticide":
            return _PESTICIDES
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
            if key in k or k in key:
                return DomainEntity(entity_type, k, dict(attrs))
        return None

    def search_entities(
        self, query: str, limit: int = 10,
    ) -> List[DomainEntity]:
        q = (query or "").strip().lower()
        if not q:
            return []
        out: List[DomainEntity] = []
        for et, table in (("crop", _CROPS), ("pesticide", _PESTICIDES)):
            for name, attrs in table.items():
                hay = f"{name} {' '.join(str(v) for v in attrs.values())}".lower()
                if q in hay:
                    out.append(DomainEntity(et, name, dict(attrs)))
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
