"""Mixin 2 of PlatformBinding."""
from __future__ import annotations
from .part1 import (Any, Dict, _pstore,)  # noqa: F401
class _Mixin2:
    def list_domains(self) -> Dict[str, Any]:
        if self._domain_registry is None:
            return {"domains": []}
        out = []
        for name in self._domain_registry.names():
            provider = self._domain_registry.resolve(name)
            out.append({
                "name": name,
                "entity_types": provider.list_entity_types(),
                "terms": len(provider.list_terms()),
            })
        return {"domains": out}

    def _mirror(self, d: Dict[str, Any], *, session_id: str = "",
                workspace: str = "", model: str = "",
                user_id: str = "") -> None:
        try:
            _pstore.save(d, session_id=session_id, workspace=workspace,
                         model=model, user_id=user_id)
        except Exception:
            pass  # 不阻塞主流程

    def list_proposals(self, payload: Dict[str, Any] | None = None
                       ) -> Dict[str, Any]:
        p = payload or {}
        items = _pstore.list_all(
            status=str(p.get("status") or ""),
            user_id=str(p.get("user_id") or ""),
            limit=int(p.get("limit") or 100),
        )
        return {"items": items, "count": len(items),
                "source": "persistent"}

    def delete_proposal(self, proposal_id: str) -> Dict[str, Any]:
        return {"deleted": _pstore.delete(proposal_id)}

    @staticmethod
    def _ids(payload: Dict[str, Any]) -> tuple:
        session_id = str(payload.get("session_id", "")).strip()
        proposal_id = str(payload.get("proposal_id", "")).strip()
        if not session_id:
            raise ValueError("session_id required")
        if not proposal_id:
            raise ValueError("proposal_id required")
        return session_id, proposal_id

    def ready(self) -> bool:
        # lazy 模式：只要 factory 存在就 ready
        return self._platform is not None or self._factory is not None

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
            "has_gateway": self._gateway is not None,
            "has_router": self._router is not None,
            "has_model_catalog": self._model_catalog is not None,
            "has_domain_registry": self._domain_registry is not None,
        }

    async def apply_adapter(
        self, payload: Dict[str, Any], wait: bool = True,
    ) -> Dict[str, Any]:
        """应用提案（工业级：async task_id + WS 订阅 / 同步 wait）。"""
        proposal_id = str(payload.get("proposal_id", "")).strip()
        if not proposal_id:
            raise ValueError("proposal_id required")

        proposal = self.platform.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(f"proposal not found: {proposal_id}")

        if wait:
            return self.platform.apply_proposal(proposal_id)

        import asyncio as _aio
        from backend.platform.apply_hub import get_apply_hub

        hub = get_apply_hub()
        tid = hub.create(proposal_id)

        def _on_step(ev: dict) -> None:
            hub.publish(tid, ev)

        async def _runner() -> None:
            try:
                def _run_sync() -> dict:
                    return self.platform.apply_proposal(
                        proposal_id, on_step=_on_step,
                    )
                result = await _aio.to_thread(_run_sync)
                ok = bool(result.get("success", False))
                hub.finish(
                    tid, "succeeded" if ok else "failed",
                    {"ok": ok, "result": result},
                )
            except Exception as exc:
                hub.publish(tid, {"type": "error", "message": str(exc)[:300]})
                hub.finish(tid, "failed", {"ok": False, "error": str(exc)})

        _aio.create_task(_runner())
        return {"task_id": tid, "proposal_id": proposal_id,
                "status": "pending", "async": True}
