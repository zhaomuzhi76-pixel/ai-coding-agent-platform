"""RAG Pipeline 三阶段流水线（自下而上分层）：
  queue               → 持久化任务队列（SQLite）
  resource_budget     → GPU 预算账本（register/unregister）
  resource_probe      → 实时资源探测（复用 system_monitor_router）
  job_classifier      → 按页数分级（light/medium/heavy）
  job_resource_estimator → 按页数估需求
  admission_policy    → 探测 + 估算 → 准入判决
  stage_ocr           → OCR 阶段（含真实判决）
  stage_embed         → Embed 阶段
  stage_vecwrite      → 向量写入阶段
  scheduler           → 装配与调度
"""
from backend.rag.ingest.pipeline.queue import (
    PipelineQueue, STAGES,
    STATUS_PENDING, STATUS_RUNNING, STATUS_DONE, STATUS_FAILED)
from backend.rag.ingest.pipeline.resource_budget import (
    GpuBudget, get_budget)
from backend.rag.ingest.pipeline.scheduler import (
    PipelineScheduler, get_scheduler, set_scheduler)
from backend.rag.ingest.pipeline.job_classifier import (
    classify, thresholds as classifier_thresholds,
    LEVEL_LIGHT, LEVEL_MEDIUM, LEVEL_HEAVY)
from backend.rag.ingest.pipeline.job_resource_estimator import (
    estimate, EstimatedDemand, thresholds as est_thresholds)
from backend.rag.ingest.pipeline.resource_probe import (
    probe, invalidate, ResourceSnapshot)
from backend.rag.ingest.pipeline.admission_policy import (
    evaluate, evaluate_and_probe, thresholds as admit_thresholds,
    AdmissionDecision)

__all__ = [
    "PipelineQueue", "STAGES",
    "STATUS_PENDING", "STATUS_RUNNING", "STATUS_DONE", "STATUS_FAILED",
    "GpuBudget", "get_budget",
    "PipelineScheduler", "get_scheduler", "set_scheduler",
    "classify", "classifier_thresholds",
    "LEVEL_LIGHT", "LEVEL_MEDIUM", "LEVEL_HEAVY",
    "estimate", "EstimatedDemand", "est_thresholds",
    "probe", "invalidate", "ResourceSnapshot",
    "evaluate", "evaluate_and_probe", "admit_thresholds", "AdmissionDecision",
]

__all__ += ["IdleReaper", "is_idle"]

from backend.rag.ingest.pipeline.idle_signals import (
    is_task_idle, check_hardware_idle)
from backend.rag.ingest.pipeline.idle_reaper import IdleReaper
__all__ += ["IdleReaper", "is_task_idle", "check_hardware_idle"]
