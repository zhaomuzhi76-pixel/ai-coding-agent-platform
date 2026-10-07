from __future__ import annotations
from typing import Any
class ApplicationStartupSupport:
    VERSION = "3.1"
    @staticmethod
    def validate_manager(manager: Any) -> Any:
        if manager is None:
            raise ValueError("capability manager required")
        if not callable(getattr(manager, "ready", None)):
            raise TypeError(
                "capability manager must expose ready()"
            )
        if not manager.ready():
            raise RuntimeError(
                "capability manager not ready"
            )
        return manager
    @staticmethod
    def require_runtime(context: dict[str, Any]) -> Any:
        runtime = context.get("runtime")
        if runtime is None:
            raise RuntimeError(
                "runtime construction required"
            )
        return runtime
    @staticmethod
    def require_agent_service(context: dict[str, Any]) -> Any:
        service = context.get("agent_service")
        if service is None:
            raise RuntimeError(
                "application agent service required"
            )
        return service
    @staticmethod
    def require_project_session_service(
        composition: Any,
        project_registry: Any,
    ) -> Any:
        if project_registry is None:
            raise RuntimeError(
                "shared project registry unavailable"
            )
        service = composition.create(
            project_registry=project_registry
        ).get("session_service")
        if service is None:
            raise RuntimeError(
                "project session service unavailable"
            )
        return service
    @staticmethod
    def validate_context(
        context: dict[str, object],
    ) -> None:
        if not isinstance(context, dict):
            raise TypeError("startup context must dict")
    @classmethod
    def capability_enabled(
        cls,
        manager: Any,
        key: str,
    ) -> bool:
        if manager is None or not key:
            return False
        name = cls._capability_name(key)
        try:
            state = manager.state(name)
        except (KeyError, LookupError, RuntimeError):
            return False
        return getattr(state, "value", None) == "enabled"
    @staticmethod
    def _capability_name(key: str) -> str:
        value = str(key).strip().split(":", 1)[0]
        if value.startswith("application."):
            value = value[len("application."):]
        return value
    @classmethod
    def assembled(
        cls,
        *,
        registry: Any,
        runtime: Any,
        agent_service: Any,
        capability_manager: Any,
        agent_capability_key: str,
        planning_binding: Any,
        planning_capability_key: str,
        code_intelligence_binding: Any = None,
        code_intelligence_capability_key: str | None = None,
        tool_binding: Any = None,
        tool_capability_key: str | None = None,
    ) -> bool:
        objects = (
            ("registry", registry),
            ("runtime", runtime),
            ("agent_service", agent_service),
            ("capability_manager", capability_manager),
            ("planning_binding", planning_binding),
        )
        for name, value in objects:
            if value is None:
                raise RuntimeError(
                    f"startup assembly missing: {name}"
                )
            if not callable(getattr(value, "ready", None)):
                raise TypeError(
                    f"{name} must expose ready()"
                )
            if not value.ready():
                raise RuntimeError(
                    f"startup assembly not ready: {name}"
                )
        required = (
            ("agent", agent_capability_key),
            ("planning", planning_capability_key),
        )
        optional = (
            (
                "code_intelligence",
                code_intelligence_binding,
                code_intelligence_capability_key,
            ),
            (
                "tool",
                tool_binding,
                tool_capability_key,
            ),
        )
        for name, key in required:
            if not cls.capability_enabled(
                capability_manager,
                key,
            ):
                raise RuntimeError(
                    "startup capability not enabled: "
                    f"{name} key={key} "
                    f"name={cls._capability_name(key)}"
                )
        for name, binding, key in optional:
            if binding is None:
                continue
            if not binding.ready():
                raise RuntimeError(
                    f"startup binding not ready: {name}"
                )
            if key and not cls.capability_enabled(
                capability_manager,
                key,
            ):
                raise RuntimeError(
                    "startup capability not enabled: "
                    f"{name} key={key} "
                    f"name={cls._capability_name(key)}"
                )
        return True
    @staticmethod
    def unload(
        manager: Any,
        key: str,
    ) -> None:
        if manager is None or not key:
            return
        try:
            manager.unload(
                ApplicationStartupSupport._capability_name(
                    key
                )
            )
        except (KeyError, LookupError, RuntimeError):
            pass
    @staticmethod
    def dump(
        *,
        name: str,
        version: str,
        started: bool,
        runtime: Any,
        capability_manager: Any,
        planning_binding: Any,
        registry: Any,
        ready: bool,
        code_intelligence_binding: Any = None,
        tool_binding: Any = None,
    ) -> dict[str, object]:
        result = {
            "name": name,
            "version": version,
            "started": started,
            "runtime": (
                runtime.dump() if runtime is not None else None
            ),
            "capability_manager": (
                capability_manager.dump()
                if capability_manager is not None
                else None
            ),
            "planning_binding": planning_binding.dump(),
            "registry": registry.dump(),
            "ready": ready,
        }
        if code_intelligence_binding is not None:
            result["code_intelligence_binding"] = (
                code_intelligence_binding.dump()
            )
        if tool_binding is not None:
            result["tool_binding"] = tool_binding.dump()
        return result
__all__ = ["ApplicationStartupSupport"]
