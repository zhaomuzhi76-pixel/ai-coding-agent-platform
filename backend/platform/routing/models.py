"""UserRouting: 用户执行时选择的模型配置。

两种模式：
    simple   单一模型覆盖所有角色
    per_role 每个角色独立选择
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


ROLES = ("intent", "plan", "code", "review", "complex")


@dataclass
class RoleRef:
    provider: str
    model: str

    def to_dict(self) -> Dict[str, str]:
        return {"provider": self.provider, "model": self.model}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RoleRef":
        return cls(
            provider=str(d.get("provider", "")).strip(),
            model=str(d.get("model", "")).strip(),
        )


@dataclass
class UserRouting:
    mode: str = "default"    # default | simple | per_role
    override_model: str = ""  # simple 模式：总模型 id
    per_role: Dict[str, RoleRef] = field(default_factory=dict)

    def validate(self) -> None:
        if self.mode not in ("default", "simple", "per_role"):
            raise ValueError(f"invalid mode: {self.mode}")
        if self.mode == "simple" and not self.override_model.strip():
            raise ValueError("simple mode requires override_model")
        if self.mode == "per_role":
            for role in ROLES:
                if role not in self.per_role:
                    raise ValueError(f"per_role missing role: {role}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "override_model": self.override_model,
            "per_role": {k: v.to_dict() for k, v in self.per_role.items()},
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "UserRouting":
        pr = d.get("per_role") or {}
        return cls(
            mode=str(d.get("mode", "default")).strip(),
            override_model=str(d.get("override_model", "")).strip(),
            per_role={
                k: RoleRef.from_dict(v)
                for k, v in pr.items()
                if isinstance(v, dict)
            },
        )


__all__ = ["ROLES", "RoleRef", "UserRouting"]
