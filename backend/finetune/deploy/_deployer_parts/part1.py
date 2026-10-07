"""Part 1 of deployer.py."""
from __future__ import annotations

import asyncio

import shutil

import subprocess

import time

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Callable

from ..modelfile import build_modelfile, _suggest_name

from ..spec import AdapterSpec

DEFAULT_TIMEOUT_SEC = 600.0

OLLAMA_BIN = "ollama"

@dataclass
class DeployPlan:
    adapter_id: str
    model_name: str
    modelfile_text: str
    modelfile_path: str
    command: list
    timeout_sec: float = DEFAULT_TIMEOUT_SEC
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "model_name": self.model_name,
            "modelfile_text": self.modelfile_text,
            "modelfile_path": self.modelfile_path,
            "command": list(self.command),
            "timeout_sec": self.timeout_sec,
            "extra": dict(self.extra),
        }

@dataclass
class DeployResult:
    ok: bool
    adapter_id: str
    model_name: str
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    elapsed_sec: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok, "adapter_id": self.adapter_id,
            "model_name": self.model_name, "returncode": self.returncode,
            "stdout": self.stdout[-2000:], "stderr": self.stderr[-2000:],
            "elapsed_sec": round(self.elapsed_sec, 2),
            "error": self.error,
        }

def is_ollama_available() -> bool:
    return shutil.which(OLLAMA_BIN) is not None

def build_deploy_plan(
    spec: AdapterSpec,
    *,
    output_dir: str | None = None,
    extra_parameters: tuple | None = None,
) -> DeployPlan:
    """生成部署计划（不执行）。"""
    if not isinstance(spec, AdapterSpec):
        raise TypeError("spec must AdapterSpec")

    model_name = spec.ollama_model_name or _suggest_name(spec)

    # Modelfile 文本
    mf_text = build_modelfile(
        from_base=spec.base_model,
        adapter_path=spec.adapter_path,
        parameters=extra_parameters,
    )

    # Modelfile 落盘位置：adapter 目录同级
    if output_dir:
        mf_dir = Path(output_dir)
    else:
        mf_dir = Path(spec.adapter_path).parent
    mf_dir.mkdir(parents=True, exist_ok=True)
    mf_path = mf_dir / ("Modelfile." + model_name.replace(":", "_").replace("/", "_"))
    mf_path.write_text(mf_text, encoding="utf-8")

    command = [OLLAMA_BIN, "create", model_name, "-f", str(mf_path)]
    return DeployPlan(
        adapter_id=spec.adapter_id,
        model_name=model_name,
        modelfile_text=mf_text,
        modelfile_path=str(mf_path),
        command=command,
    )

def _run_sync(
    plan: DeployPlan,
    on_log: Callable[[str], None] | None = None,
) -> DeployResult:
    t0 = time.time()
    try:
        proc = subprocess.run(
            plan.command,
            capture_output=True,
            text=True,
            timeout=plan.timeout_sec,
        )
        elapsed = time.time() - t0
        if on_log:
            try: on_log(proc.stdout)
            except Exception: pass
        return DeployResult(
            ok=(proc.returncode == 0),
            adapter_id=plan.adapter_id,
            model_name=plan.model_name,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            elapsed_sec=elapsed,
            error="" if proc.returncode == 0 else (
                "ollama create failed: " + (proc.stderr or "")[:300]
            ),
        )
    except subprocess.TimeoutExpired:
        return DeployResult(
            ok=False, adapter_id=plan.adapter_id, model_name=plan.model_name,
            elapsed_sec=time.time() - t0,
            error=f"timeout after {plan.timeout_sec}s",
        )
    except FileNotFoundError:
        return DeployResult(
            ok=False, adapter_id=plan.adapter_id, model_name=plan.model_name,
            elapsed_sec=time.time() - t0,
            error="ollama binary not found",
        )
    except Exception as exc:
        return DeployResult(
            ok=False, adapter_id=plan.adapter_id, model_name=plan.model_name,
            elapsed_sec=time.time() - t0,
            error=f"{type(exc).__name__}: {exc}",
        )

async def run_deploy(
    plan: DeployPlan,
    on_log: Callable[[str], None] | None = None,
) -> DeployResult:
    """异步执行部署（to_thread 避免阻塞事件循环）。"""
    if not isinstance(plan, DeployPlan):
        raise TypeError("plan must DeployPlan")
    return await asyncio.to_thread(_run_sync, plan, on_log)
