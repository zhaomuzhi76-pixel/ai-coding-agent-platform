"""准入判决。职责：实时探测 + 估算需求 → 是否放行。
不探测（resource_probe 管）、不估算（job_resource_estimator 管）。
环境变量（全部可调，无硬编码）：
  RAG_ADMIT_GPU_SAFETY_MB=500      显存安全垫
  RAG_ADMIT_MEM_SAFETY_MB=500      内存安全垫
  RAG_ADMIT_MAX_CPU_PERCENT=85.0   CPU 使用率上限
  RAG_ADMIT_MAX_GPU_UTIL=90        GPU 利用率上限
  RAG_ADMIT_MAX_GPU_TEMP_C=85      GPU 温度上限
  RAG_ADMIT_REQUIRE_GPU=1          是否必须有可用 GPU
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any, List, Optional


def _env_i(key: str, default: str) -> int:
    return int(os.environ.get(key, default))


def _env_f(key: str, default: str) -> float:
    return float(os.environ.get(key, default))


@dataclass(frozen=True)
class AdmissionDecision:
    allow: bool
    reasons: List[str] = field(default_factory=list)
    snapshot: Any = None
    demand: Any = None

    def to_dict(self) -> dict:
        return {
            "allow": self.allow,
            "reasons": list(self.reasons),
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
            "demand": self.demand.to_dict() if self.demand else None,
        }


def thresholds() -> dict:
    return {
        "gpu_safety_mb": _env_i("RAG_ADMIT_GPU_SAFETY_MB", "500"),
        "mem_safety_mb": _env_i("RAG_ADMIT_MEM_SAFETY_MB", "500"),
        "max_cpu_percent": _env_f("RAG_ADMIT_MAX_CPU_PERCENT", "85.0"),
        "max_gpu_util": _env_i("RAG_ADMIT_MAX_GPU_UTIL", "90"),
        "max_gpu_temp_c": _env_i("RAG_ADMIT_MAX_GPU_TEMP_C", "85"),
        "require_gpu": _env_i("RAG_ADMIT_REQUIRE_GPU", "1") == 1,
    }


def _check_gpu(snap: Any, dem: Any, env: dict) -> List[str]:
    out: List[str] = []
    if env["require_gpu"] and not snap.gpu_ok:
        out.append(f"gpu_unavailable({snap.error})")
        return out
    if not snap.gpu_ok:
        return out  # 无 GPU 但允许降级
    need_total = dem.ocr_gpu_mb + env["gpu_safety_mb"]
    if snap.gpu_free_mb < need_total:
        out.append(f"gpu_free({snap.gpu_free_mb})<need({need_total})")
    if snap.gpu_util > env["max_gpu_util"]:
        out.append(f"gpu_util({snap.gpu_util})>{env['max_gpu_util']}")
    if snap.gpu_temp_c > env["max_gpu_temp_c"]:
        out.append(f"gpu_temp({snap.gpu_temp_c})>{env['max_gpu_temp_c']}")
    return out


def _check_mem(snap: Any, dem: Any, env: dict) -> List[str]:
    need = dem.mem_mb + env["mem_safety_mb"]
    if snap.mem_available_mb < need:
        return [f"mem_avail({snap.mem_available_mb})<need({need})"]
    return []


def _check_cpu(snap: Any, env: dict) -> List[str]:
    if snap.cpu_percent > env["max_cpu_percent"]:
        return [f"cpu_percent({snap.cpu_percent})>{env['max_cpu_percent']}"]
    return []


def evaluate(snapshot: Any, demand: Any,
             env: Optional[dict] = None) -> AdmissionDecision:
    """用探测快照 + 需求估算 → 判决。
    所有阈值来自 thresholds()（env 驱动）。
    """
    e = env or thresholds()
    reasons: List[str] = []
    reasons.extend(_check_gpu(snapshot, demand, e))
    reasons.extend(_check_mem(snapshot, demand, e))
    reasons.extend(_check_cpu(snapshot, e))
    return AdmissionDecision(
        allow=(len(reasons) == 0),
        reasons=reasons, snapshot=snapshot, demand=demand)


def evaluate_and_probe(demand: Any) -> AdmissionDecision:
    """便捷入口：自动 probe() + evaluate()。"""
    from backend.rag.ingest.pipeline.resource_probe import probe
    snap = probe()
    return evaluate(snap, demand)


__all__ = ["AdmissionDecision", "evaluate", "evaluate_and_probe", "thresholds"]
