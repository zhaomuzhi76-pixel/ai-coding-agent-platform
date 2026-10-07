"""AgentSpec: 子进程绑定的 provider/model/workspace 规格。

契约：
  - frozen + slots（不可变，spawn 前定型）
  - agent_id / provider / model 必填非空
  - to_dict/from_dict 往返一致

不负责：
  - IPC 传输 / 进程管理 / gateway 构造
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentSpec:
    agent_id: str
    provider: str
    model: str
    workspace: str = ""
    base_url: str = ""
    api_key: str = ""
    max_steps: int = 10
    extra_env: tuple = ()

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for name in ("agent_id", "provider", "model"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise ValueError("AgentSpec." + name + " required")
        if not isinstance(self.max_steps, int) or self.max_steps <= 0:
            raise ValueError("AgentSpec.max_steps must be positive int")
        if not isinstance(self.extra_env, tuple):
            raise TypeError("AgentSpec.extra_env must be tuple")

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "provider": self.provider,
            "model": self.model,
            "workspace": self.workspace,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "max_steps": self.max_steps,
            "extra_env": [list(p) for p in self.extra_env],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AgentSpec":
        raw = d.get("extra_env") or ()
        if isinstance(raw, dict):
            extra = tuple((str(k), str(v)) for k, v in raw.items())
        else:
            extra = tuple((str(x[0]), str(x[1])) for x in raw)
        return cls(
            agent_id=str(d.get("agent_id", "")),
            provider=str(d.get("provider", "")),
            model=str(d.get("model", "")),
            workspace=str(d.get("workspace", "")),
            base_url=str(d.get("base_url", "")),
            api_key=str(d.get("api_key", "")),
            max_steps=int(d.get("max_steps", 10)),
            extra_env=extra,
        )

    def to_env(self) -> dict[str, str]:
        env = {
            "LOCO_AGENT_ID": self.agent_id,
            "LOCO_AGENT_PROVIDER": self.provider,
            "LOCO_AGENT_MODEL": self.model,
            "LOCO_WORKER_ACTIVE": "1",
        }
        for k, v in self.extra_env:
            env[k] = v
        return env


__all__ = ["AgentSpec"]
