"""Mixin 1 of PlatformBinding."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Any, Callable, CodingPlatform, CodingRequest, Dict, Optional,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        platform: Optional[CodingPlatform] = None,
        *,
        platform_factory: Optional[Callable[[], CodingPlatform]] = None,
        gateway: Any = None,
        router: Any = None,
        model_catalog: Any = None,
        domain_registry: Any = None,
    ) -> None:
        if platform is None and platform_factory is None:
            raise ValueError(
                "platform or platform_factory required"
            )
        self._platform = platform
        self._factory = platform_factory
        self._gateway = gateway
        self._router = router
        self._model_catalog = model_catalog
        self._domain_registry = domain_registry
        try:
            from backend.platform.routing import RoutingStore
            self._routing_store = RoutingStore()
        except Exception:
            self._routing_store = None

    @property
    def platform(self) -> CodingPlatform:
        if self._platform is None:
            if self._factory is None:
                raise RuntimeError("platform factory missing")
            self._platform = self._factory()
        return self._platform

    def create_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        workspace = str(payload.get("workspace", "")).strip()
        if not workspace:
            raise ValueError("workspace required")
        s = self.platform.create_session(
            workspace=workspace,
            user_id=str(payload.get("user_id", "")),
            locale=str(payload.get("locale", "zh-CN")),
            model=str(payload.get("model", "")),
        )
        return {
            "session_id": s.session_id,
            "workspace": s.workspace,
            "user_id": s.user_id,
            "locale": s.locale,
            "model": s.model,
        }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if not session_id or not session_id.strip():
            raise ValueError("session_id required")
        s = self.platform.get_session(session_id.strip())
        return {
            "session_id": s.session_id,
            "workspace": s.workspace,
            "user_id": s.user_id,
            "locale": s.locale,
            "model": s.model,
            "turn_count": s.turn_count(),
        }

    async def propose(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            raise ValueError("session_id required")
        req = CodingRequest.from_dict(payload)
        gateway = self._resolve_gateway()
        router = self._resolve_router(payload)
        proposal = await self.platform.propose(
            session_id, req,
            gateway=gateway, router=router,
        )
        d = proposal.to_dict()
        self._mirror(d, session_id=session_id,
                     workspace=str(payload.get("workspace") or ""),
                     model=str(payload.get("model") or ""),
                     user_id=str(payload.get("user_id") or ""))
        return d

    def _resolve_gateway(self):
        """优先用构造时注入的；否则从 runtime_deps 动态取。"""
        if self._gateway is not None:
            return self._gateway
        try:
            from backend.runtime.executors.runtime_dependencies import (
                get_runtime_deps,
            )
            deps = get_runtime_deps()
            gw = deps.get("gateway")
            if gw is not None:
                self._gateway = gw
                return gw
        except Exception as e:
            swallow("api.platform._binding_parts.mixin1:104", e, level="warn")
        return self._gateway

    def _resolve_router(self, payload: Dict[str, Any]):
        """若 payload.model 与当前 router override 不同，造一个新的 override router。"""
        user_model = str(payload.get("model", "")).strip()
        if not user_model:
            return self._router
        base = self._router
        existing = (
            getattr(base, "_override_model", None) if base else None
        )
        if existing == user_model:
            return base
        try:
            from backend.application.provider_gateway.model_router import (
                ModelRouter,
            )
            return ModelRouter(override_model=user_model)
        except Exception:
            return base

    def approve(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id, proposal_id = self._ids(payload)
        self.platform.approve(session_id, proposal_id)
        d = self.platform.proposal(proposal_id).to_dict()
        self._mirror(d, session_id=session_id)
        return d

    def reject(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id, proposal_id = self._ids(payload)
        reason = str(payload.get("reason", ""))
        self.platform.reject(session_id, proposal_id, reason)
        d = self.platform.proposal(proposal_id).to_dict()
        self._mirror(d, session_id=session_id)
        return d

    def apply(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id, proposal_id = self._ids(payload)
        result = self.platform.apply(session_id, proposal_id)
        pd = self.platform.proposal(proposal_id).to_dict()
        self._mirror(pd, session_id=session_id)
        return {"proposal": pd, "result": result}

    def verify(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id, proposal_id = self._ids(payload)
        workspace = str(payload.get("workspace", ""))
        result = self.platform.verify(session_id, proposal_id, workspace)
        pd = self.platform.proposal(proposal_id).to_dict()
        self._mirror(pd, session_id=session_id)
        return {"proposal": pd, "result": result}

    def learn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id, proposal_id = self._ids(payload)
        self.platform.learn(session_id, proposal_id)
        d = self.platform.proposal(proposal_id).to_dict()
        self._mirror(d, session_id=session_id)
        return {"proposal_id": proposal_id, "learned": True}

    def list_models(self) -> Dict[str, Any]:
        if self._model_catalog is None:
            return {"models": []}
        return {
            "models": [
                o.to_dict() for o in self._model_catalog.list()
            ]
        }

    def get_routing(self, user_id: str = "default") -> Dict[str, Any]:
        if self._routing_store is None:
            return {"routing": None}
        r = self._routing_store.load(user_id)
        return {"routing": r.to_dict()}

    def set_routing(
        self, user_id: str, payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self._routing_store is None:
            raise RuntimeError("routing store unavailable")
        from backend.platform.routing import UserRouting
        r = UserRouting.from_dict(payload)
        r.validate()
        self._routing_store.save(user_id, r)
        return {"saved": True, "routing": r.to_dict()}

    def reset_routing(self, user_id: str = "default") -> Dict[str, Any]:
        if self._routing_store is None:
            return {"reset": False}
        self._routing_store.reset(user_id)
        return {"reset": True}
