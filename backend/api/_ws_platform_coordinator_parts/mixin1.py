"""Mixin 1 of PlatformBackedCoordinator."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Any, Dict, ResultSerializer, WSMessageSender, dispatch, normalize_only, normalize_workspace_path, run_team_if_configured, to_runtime_event_v2,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        sender: WSMessageSender | None = None,
        serializer: ResultSerializer | None = None,
    ) -> None:
        self.sender = sender or WSMessageSender()
        self.serializer = serializer or ResultSerializer()
        self.execution_count = 0
        self.failure_count = 0
        self._binding = None

    def _get_binding(self):
        """惰性构造 PlatformBinding。"""
        if self._binding is not None:
            return self._binding
        from backend.api.platform.binding import PlatformBinding
        from backend.api.platform.factory import (
            _build_platform, _build_catalog, _build_domain_registry,
        )
        try:
            from backend.runtime.executors.runtime_dependencies import (
                get_runtime_deps,
            )
            deps = get_runtime_deps()
        except Exception:
            deps = {}
        self._binding = PlatformBinding(
            platform_factory=_build_platform,
            model_catalog=_build_catalog(),
            domain_registry=_build_domain_registry(),
            gateway=deps.get("gateway"),
            router=deps.get("router"),
        )
        return self._binding

    async def execute(
        self,
        websocket: object,
        transport_session_id: str,
        execution_session_id: str,
        payload: Dict[str, Any],
    ) -> None:
        """收到 WS 请求 → 调 PlatformBinding.propose → 回发结果。

        payload 字段（兼容旧协议）：
            session_id, message, provider, model, workspace, base_url, api_key
        """
        # ── 工业级单一入口：payload 一次清洗，下游全拿干净路径 ──
        if isinstance(payload, dict):
            raw_ws = str(payload.get("workspace", "") or "")
            if raw_ws:
                payload = {**payload, "workspace": normalize_only(raw_ws)}

        binding = self._get_binding()
        user_model = str(payload.get("model", "")).strip()
        _domains = payload.get("domains") or []
        print(f"[ws-coordinator] domains={_domains} "
              f"message={str(payload.get('message',''))[:50]!r}",
              flush=True)

        # 1. 确保有 session
        try:
            existing = binding.get_session(execution_session_id)
        except (KeyError, Exception):
            existing = None

        if existing is None:
            ws = str(payload.get("workspace", "")).strip()
            if not ws:
                await self._fail(
                    websocket, transport_session_id, user_model,
                    "workspace required",
                )
                return
            created = binding.create_session({
                "workspace": ws,
                "user_id": "default",
                "locale": "zh-CN",
                "model": user_model,
            })
            execution_session_id = created["session_id"]

        # ── 审批消息优先处理（不进入 agent_loop）──
        action = str(payload.get("action", "")).strip()
        if action in ("approve", "reject"):
            edit_id = str(payload.get("edit_id", "")).strip()
            from backend.application.agent_loop.pending_gate import get_gate
            gate = get_gate()
            if action == "approve":
                ok = await gate.approve(edit_id)
            else:
                ok = await gate.reject(edit_id)
            await self._send(
                websocket, transport_session_id, user_model,
                {"success": bool(ok), "action": action,
                 "edit_id": edit_id},
            )
            return

        # 提取 LLM gateway（兼容两种属性名，deps 未注入时为 None）
        gw = (getattr(binding, "_gateway", None)
              or getattr(binding, "gateway", None))

        # ── multiplex 分支：env 未设 → None，走原路径；设了 → 多 agent 走完 ──
        try:
            multiplex_result = await run_team_if_configured({
                "message": str(payload.get("message", "")),
                "session_id": transport_session_id,
                "workspace": str(payload.get("workspace", "")),
            })
        except Exception as exc:
            multiplex_result = None
            print(
                "[multiplex] entry error: "
                + type(exc).__name__ + ": " + str(exc),
                flush=True,
            )

        if multiplex_result is not None:
            await self._send(
                websocket, transport_session_id, user_model,
                multiplex_result,
            )
            return

        # 把 agent_loop 的每一步推成 WS step 消息
        async def _emit_step(entry: dict) -> None:
            """直发原始 step 帧（不走 sender.send_result，避免双重包装）。"""
            # 1) WS 已断？跳过
            try:
                from starlette.websockets import WebSocketState
                state = getattr(websocket, "client_state", None)
                if state is not None and state != WebSocketState.CONNECTED:
                    return
            except Exception as e:
                swallow("api._ws_platform_coordinator_parts.mixin1:138", e, level="warn")
            # 2) 直发原始 JSON
            try:
                await websocket.send_json({
                    "type": "step",
                    "session_id": transport_session_id,
                    "data": to_runtime_event_v2(
                        entry, transport_session_id,
                    ),
                })
            except Exception as e:
                swallow("api._ws_platform_coordinator_parts.mixin1:149", e, level="warn")


        def _on_step(entry: dict):
            # agent_loop 内同步调用；返回 coroutine 让它 await
            return _emit_step(entry)

        try:
            quick = await dispatch(
                payload, existing, gateway=gw, on_step=_on_step,
            )
        except Exception as exc:
            quick = {"success": False, "error": f"{type(exc).__name__}: {exc}"}
        if quick is not None:
            self.execution_count += 1
            await self._send(
                websocket, transport_session_id, user_model, quick,
            )
            return

        # 3. propose（原路径）
        try:
            proposal = await binding.propose({
                "session_id": execution_session_id,
                "task": str(payload.get("message", "")),
                "files": [self._guess_file(payload)],
                "workspace": payload.get("workspace", ""),
                "model": user_model,
                "locale": "zh-CN",
                "domains": payload.get("domains") or [],
            })
            self.execution_count += 1

            await self._send(
                websocket, transport_session_id, user_model,
                {
                    "success": True,
                    "proposal_id": proposal.get("proposal_id"),
                    "status": proposal.get("status"),
                    "plan": proposal.get("plan"),
                    "changes": proposal.get("changes", []),
                    "task": proposal.get("task"),
                },
            )
        except Exception as exc:
            self.failure_count += 1
            await self._fail(
                websocket, transport_session_id, user_model,
                f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _guess_file(payload: Dict[str, Any]) -> str:
        """从 message 猜主文件，缺省 'unknown.py'。"""
        msg = str(payload.get("message", ""))
        for token in msg.split():
            if token.endswith(".py"):
                return normalize_workspace_path(token.strip(",.;:"))
        return "unknown.py"
