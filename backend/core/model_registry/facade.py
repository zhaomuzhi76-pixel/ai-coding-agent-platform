"""业务门面层（Dify 风格 API）：仅暴露给 UI/前端的纯数据接口"""
from typing import Any, Dict, List, Optional

from .domain import ModelInfo, ProviderConfig, RoleRoute
from .persistence import load as _load, save as _save
from .registry import get_registry

ROLE_LABELS = {
    "intent": "意图理解", "plan": "任务规划",
    "code": "代码生成", "review": "代码审查",
    "complex": "复杂推理",
}


class RegistryFacade:
    # 延迟获取 registry 单例，避免 reset_registry() 后引用失效
    @property
    def _reg(self):
        return get_registry()

    # ---------- 引导 / 持久化 ----------
    def bootstrap(self) -> None:
        if not self._reg.providers:
            from .bootstrap import bootstrap_default
            bootstrap_default()
        _load(self._reg)

    def persist(self) -> str:
        return str(_save(self._reg))

    # ---------- Provider 卡片（左侧栏） ----------
    def provider_cards(self) -> List[Dict[str, Any]]:
        health = self._reg.health()
        return [{
            "id": p.id,
            "name": p.name,
            "kind": p.kind,
            "base_url": p.base_url,
            "has_key": bool(p.api_key),
            "enabled": p.enabled,
            "connected": health.get(p.id, False),
            "model_count": sum(
                1 for m in self._reg.models.values() if m.provider_id == p.id
            ),
            "verified_count": sum(
                1 for m in self._reg.models.values()
                if m.provider_id == p.id
                and self._reg.verification.is_verified(m.id)
            ),
        } for p in self._reg.providers.values()]

    # ---------- 模型列表（Provider 详情页） ----------
    def models_of(self, provider_id: str) -> List[Dict[str, Any]]:
        return [{
            "id": m.id, "display": m.display_name or m.id,
            "provider": m.provider_id, "ctx": m.context_window,
            "cost_per_1k": m.cost_per_1k, "tags": list(m.tags),
        } for m in self._reg.models.values()
           if m.provider_id == provider_id]

    # ---------- 角色路由卡片（Dify 风格） ----------
    def role_cards(self) -> List[Dict[str, Any]]:
        # [OPT] 已验证模型集合（chat_only=True 过滤非对话模型）
        verified_ids = set()
        try:
            for v in self._reg.list_verified_models(chat_only=True):
                verified_ids.add(v["id"])
        except Exception:
            pass

        # [OPT] 候选排序：已验证优先，其余按 id 字母序
        all_models = sorted(
            self._reg.models.values(),
            key=lambda mm: (mm.id not in verified_ids, mm.id),
        )
        candidates = [
            {"value": mm.id,
             "label": mm.display_name or mm.id,
             "group": mm.provider_id,
             "verified": mm.id in verified_ids}
            for mm in all_models
        ]

        cards = []
        for role, label in ROLE_LABELS.items():
            route = self._reg.get_role_route(role)
            primary = route.primary if route else ""
            m = self._reg.models.get(primary)
            cards.append({
                "role": role, "label": label,
                "primary": primary,
                "primary_provider": m.provider_id if m else "",
                "fallback": route.fallback if route else None,
                "ui": "select",
                "verified_count": len(verified_ids),
                "candidates": candidates,
            })
        return cards

    # ---------- 写操作 ----------
    def upsert_provider(self, cfg: ProviderConfig) -> None:
        self._reg.register_provider(cfg)
        self._reg.discover_models()
        _save(self._reg)

    def set_role(self, role: str, primary: str,
                 fallback: Optional[str] = None) -> None:
        self._reg.set_role_route(
            RoleRoute(role=role, primary=primary, fallback=fallback)
        )
        _save(self._reg)

    def test_and_verify_provider(self, provider_id: str) -> Dict[str, Any]:
        result = self._reg.test_and_verify(provider_id)
        _save(self._reg)
        return result

    def verified_models(self) -> List[Dict[str, Any]]:
        return self._reg.list_verified_models()

    def test_provider(self, provider_id: str) -> bool:
        plugin = self._reg.plugins.get(provider_id)
        return plugin.test_connection() if plugin else False

    # ---------- KPI 面板 ----------
    def kpi(self) -> Dict[str, Any]:
        return {
            "providers_total": len(self._reg.providers),
            "providers_connected": sum(
                1 for v in self._reg.health().values() if v),
            "models_total": len(self._reg.models),
            "roles_routed": sum(
                1 for r in self._reg.roles.values()
                if r.primary in self._reg.models),
        }


_facade: Optional[RegistryFacade] = None


def get_facade() -> RegistryFacade:
    global _facade
    if _facade is None:
        _facade = RegistryFacade()
    return _facade
