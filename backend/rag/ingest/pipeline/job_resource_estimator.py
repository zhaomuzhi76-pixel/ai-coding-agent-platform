"""任务资源估算器。职责：按页数/大小估算 CPU/内存/GPU 需求。
只算需求，不判决、不探测（resource_probe 管探测）。
公式全参数化（env 驱动），无裸阈值。
环境变量：
  # ── OCR 阶段（Paddle）──
  RAG_EST_OCR_BASE_GPU_MB=1500     模型加载基线（MB）
  RAG_EST_OCR_PER_PAGE_GPU_MB=1    每页临时张量增量
  RAG_EST_OCR_BASE_MEM_MB=300
  RAG_EST_OCR_PER_PAGE_MEM_MB=2
  RAG_EST_OCR_SEC_PER_PAGE=3.0     单页 OCR 预估耗时
  # ── Embed 阶段（Ollama）──
  RAG_EST_EMBED_BASE_GPU_MB=3500   模型常驻显存
  RAG_EST_CHUNKS_PER_PAGE=4        每页估算 chunk 数
  RAG_EST_EMBED_SEC_PER_BATCH=1.5  单批 embed 耗时
  RAG_EST_EMBED_BATCH=16           批大小
  # ── 冗余系数（heavy 任务预留）──
  RAG_EST_HEAVY_REDUNDANCY=1.2
  RAG_EST_MEDIUM_REDUNDANCY=1.1
  RAG_EST_LIGHT_REDUNDANCY=1.0
"""
from __future__ import annotations
import math
import os
from dataclasses import dataclass
from typing import Optional


# ── 配置常量（全部来自 env，无裸阈值）──
def _env_f(key: str, default: str) -> float:
    return float(os.environ.get(key, default))


def _env_i(key: str, default: str) -> int:
    return int(os.environ.get(key, default))


@dataclass(frozen=True)
class EstimatedDemand:
    """一个任务的资源需求估算（不可变）。"""
    level: str
    page_count: int
    size_bytes: int
    # GPU 峰值（MB）
    ocr_gpu_mb: int
    embed_gpu_mb: int
    # 内存峰值（MB）
    mem_mb: int
    # CPU 核数
    cpu_cores: int
    # 时间预估（秒）
    ocr_time_s: int
    embed_time_s: int
    # 依据（透明化，便于审计）
    reason: str

    def to_dict(self) -> dict:
        return {
            "level": self.level, "page_count": self.page_count,
            "size_bytes": self.size_bytes,
            "ocr_gpu_mb": self.ocr_gpu_mb, "embed_gpu_mb": self.embed_gpu_mb,
            "mem_mb": self.mem_mb, "cpu_cores": self.cpu_cores,
            "ocr_time_s": self.ocr_time_s, "embed_time_s": self.embed_time_s,
            "reason": self.reason,
        }


def _redundancy(level: str) -> float:
    return {
        "heavy": _env_f("RAG_EST_HEAVY_REDUNDANCY", "1.2"),
        "medium": _env_f("RAG_EST_MEDIUM_REDUNDANCY", "1.1"),
        "light": _env_f("RAG_EST_LIGHT_REDUNDANCY", "1.0"),
    }.get(level, 1.0)


def _pages_of(page_count: int) -> int:
    """防止 page_count 为 0 或负数导致估算为 0。"""
    return max(1, int(page_count or 0))


def _chunks_per_page() -> int:
    return max(1, _env_i("RAG_EST_CHUNKS_PER_PAGE", "4"))


def estimate(page_count: int,
             size_bytes: int,
             level: str = "light") -> EstimatedDemand:
    """按页数+级别估算需求。纯函数，无副作用。
    - page_count <= 0 → 视作 1 页（最小估算）
    - 结果应用级别冗余系数
    """
    pages = _pages_of(page_count)
    red = _redundancy(level)

    # OCR 阶段
    ocr_base_gpu = _env_i("RAG_EST_OCR_BASE_GPU_MB", "1500")
    ocr_per_page_gpu = _env_i("RAG_EST_OCR_PER_PAGE_GPU_MB", "1")
    ocr_base_mem = _env_i("RAG_EST_OCR_BASE_MEM_MB", "300")
    ocr_per_page_mem = _env_i("RAG_EST_OCR_PER_PAGE_MEM_MB", "2")
    sec_per_page = _env_f("RAG_EST_OCR_SEC_PER_PAGE", "3.0")

    ocr_gpu = int((ocr_base_gpu + ocr_per_page_gpu * pages) * red)
    ocr_mem = int((ocr_base_mem + ocr_per_page_mem * pages) * red)
    ocr_time = int(sec_per_page * pages)

    # Embed 阶段
    embed_base_gpu = _env_i("RAG_EST_EMBED_BASE_GPU_MB", "3500")
    embed_gpu = int(embed_base_gpu * red)

    chunks = pages * _chunks_per_page()
    batch = max(1, _env_i("RAG_EST_EMBED_BATCH", "16"))
    sec_per_batch = _env_f("RAG_EST_EMBED_SEC_PER_BATCH", "1.5")
    embed_time = int(math.ceil(chunks / batch) * sec_per_batch)

    # CPU 需求：OCR 单核 + Embed 3 线程
    cpu_cores = 1 if level == "heavy" else 2

    reason = (f"pages={pages} red={red:.2f} "
              f"ocr=base{ocr_base_gpu}+{ocr_per_page_gpu}/page "
              f"embed=base{embed_base_gpu}")

    return EstimatedDemand(
        level=level, page_count=int(page_count or 0),
        size_bytes=int(size_bytes or 0),
        ocr_gpu_mb=max(0, ocr_gpu),
        embed_gpu_mb=max(0, embed_gpu),
        mem_mb=max(0, ocr_mem),
        cpu_cores=cpu_cores,
        ocr_time_s=max(0, ocr_time),
        embed_time_s=max(0, embed_time),
        reason=reason,
    )


def thresholds() -> dict:
    """导出当前生效阈值（用于审计/调试）。"""
    return {
        "ocr": {
            "base_gpu_mb": _env_i("RAG_EST_OCR_BASE_GPU_MB", "1500"),
            "per_page_gpu_mb": _env_i("RAG_EST_OCR_PER_PAGE_GPU_MB", "1"),
            "base_mem_mb": _env_i("RAG_EST_OCR_BASE_MEM_MB", "300"),
            "per_page_mem_mb": _env_i("RAG_EST_OCR_PER_PAGE_MEM_MB", "2"),
            "sec_per_page": _env_f("RAG_EST_OCR_SEC_PER_PAGE", "3.0"),
        },
        "embed": {
            "base_gpu_mb": _env_i("RAG_EST_EMBED_BASE_GPU_MB", "3500"),
            "chunks_per_page": _chunks_per_page(),
            "batch": _env_i("RAG_EST_EMBED_BATCH", "16"),
            "sec_per_batch": _env_f("RAG_EST_EMBED_SEC_PER_BATCH", "1.5"),
        },
        "redundancy": {
            "heavy": _env_f("RAG_EST_HEAVY_REDUNDANCY", "1.2"),
            "medium": _env_f("RAG_EST_MEDIUM_REDUNDANCY", "1.1"),
            "light": _env_f("RAG_EST_LIGHT_REDUNDANCY", "1.0"),
        },
    }


__all__ = ["EstimatedDemand", "estimate", "thresholds"]
