"""验证状态管理：只有通过链路测试的模型才能进入 Agent 下拉"""
from typing import Dict, List, Set


class VerificationStore:
    def __init__(self):
        self._verified: Set[str] = set()
        self._errors: Dict[str, str] = {}

    def mark_verified(self, model_ids: List[str]) -> None:
        for mid in model_ids:
            self._verified.add(mid)
            self._errors.pop(mid, None)

    def mark_failed(self, model_id: str, error: str) -> None:
        self._verified.discard(model_id)
        self._errors[model_id] = error

    def revoke(self, model_id: str) -> None:
        self._verified.discard(model_id)

    def is_verified(self, model_id: str) -> bool:
        return model_id in self._verified

    def list_verified(self) -> List[str]:
        return sorted(self._verified)

    def error_of(self, model_id: str) -> str:
        return self._errors.get(model_id, "")

    def export(self) -> Dict:
        return {"verified": sorted(self._verified), "errors": dict(self._errors)}

    def load(self, data: Dict) -> None:
        self._verified = set(data.get("verified", []))
        self._errors = dict(data.get("errors", {}))
