"""训练环境检测（D · 纯函数，只读）。

职责：
    - 检测 torch / cuda / peft / transformers / bitsandbytes 是否可用
    - 检测 GPU 型号 + 显存
    - 给出"能否真训"判定 + 未装时的安装指引

不负责：
    - 安装依赖（用户手动）
    - 跑训练（backend 管）
    - HTTP（api 管）

零副作用：只 import + 探测，不下载/不占资源。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import importlib
import shutil
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PackageStatus:
    name: str
    installed: bool
    version: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "installed": self.installed,
            "version": self.version,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class GpuStatus:
    available: bool
    name: str = ""
    vram_total_mb: int = 0
    vram_free_mb: int = 0
    compute_capability: str = ""
    cuda_version: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "name": self.name,
            "vram_total_mb": self.vram_total_mb,
            "vram_free_mb": self.vram_free_mb,
            "compute_capability": self.compute_capability,
            "cuda_version": self.cuda_version,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class EnvReport:
    ready_for_training: bool
    packages: tuple
    gpu: GpuStatus
    ollama_available: bool
    suggestions: tuple = ()
    warnings: tuple = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready_for_training": self.ready_for_training,
            "packages": [p.to_dict() for p in self.packages],
            "gpu": self.gpu.to_dict(),
            "ollama_available": self.ollama_available,
            "suggestions": list(self.suggestions),
            "warnings": list(self.warnings),
        }


# ── 包探测（唯一来源）──
_REQUIRED = (
    "torch",
    "transformers",
    "peft",
    "datasets",
    "accelerate",
    "bitsandbytes",
)


def _probe_package(name: str) -> PackageStatus:
    try:
        mod = importlib.import_module(name)
        return PackageStatus(
            name=name,
            installed=True,
            version=str(getattr(mod, "__version__", "?")),
        )
    except ImportError as exc:
        return PackageStatus(name=name, installed=False, error=str(exc))
    except Exception as exc:
        return PackageStatus(
            name=name, installed=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def _probe_gpu() -> GpuStatus:
    try:
        import torch
    except ImportError as exc:
        return GpuStatus(available=False, error=f"torch missing: {exc}")
    try:
        if not torch.cuda.is_available():
            return GpuStatus(available=False, error="cuda not available")
        idx = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(idx)
        free_b = 0
        try:
            free_b, _ = torch.cuda.mem_get_info(idx)
        except Exception as e:
            swallow("finetune.env_check:124", e)
        total_mb = int(props.total_memory // 1024 // 1024)
        free_mb = int(free_b // 1024 // 1024) if free_b else 0
        return GpuStatus(
            available=True,
            name=str(props.name),
            vram_total_mb=total_mb,
            vram_free_mb=free_mb,
            compute_capability=f"{props.major}.{props.minor}",
            cuda_version=str(getattr(torch.version, "cuda", "") or ""),
        )
    except Exception as exc:
        return GpuStatus(
            available=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def _ollama_ok() -> bool:
    return shutil.which("ollama") is not None


def check_env() -> EnvReport:
    """一次性检测（幂等，只读）。"""
    packages = tuple(_probe_package(n) for n in _REQUIRED)
    gpu = _probe_gpu()
    ollama_ok = _ollama_ok()

    missing = [p.name for p in packages if not p.installed]
    suggestions: list[str] = []
    warnings: list[str] = []

    if missing:
        suggestions.append(
            "pip install torch --index-url "
            "https://download.pytorch.org/whl/cu126"
        )
        rest = [m for m in missing if m != "torch"]
        if rest:
            suggestions.append("pip install " + " ".join(rest))

    if not gpu.available:
        warnings.append(
            "GPU 不可用：训练会回退 CPU（慢但能跑通流程）"
        )

    ready = (not missing) and gpu.available

    if ready and gpu.vram_total_mb < 6000:
        warnings.append(
            f"显存 {gpu.vram_total_mb}MB 偏小："
            f"建议 0.5B/1.5B QLoRA，>3B 可能 OOM"
        )

    return EnvReport(
        ready_for_training=ready,
        packages=packages,
        gpu=gpu,
        ollama_available=ollama_ok,
        suggestions=tuple(suggestions),
        warnings=tuple(warnings),
    )


__all__ = [
    "PackageStatus", "GpuStatus", "EnvReport",
    "check_env", "_REQUIRED",
]
