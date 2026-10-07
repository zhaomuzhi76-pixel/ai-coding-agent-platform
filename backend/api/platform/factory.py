"""Factory: build the platform router for app assembly.

接线：
    yaml LLM 配置 → ModelCatalog (前端可选模型)
    agent.tools.domain → DomainRegistry
    lazy 从 runtime deps 构造真 CodingPlatform（bootstrap 之后）
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import logging
from typing import Any

from fastapi import APIRouter

from backend.api.platform.binding import PlatformBinding
from backend.api.platform.router import PlatformRouter

logger = logging.getLogger(__name__)


def _build_catalog() -> Any:
    """从 llm_providers.yaml 构造 ModelCatalog。"""
    try:
        from backend.providers.config import build_all
        built = build_all()
        catalog = built["catalog"]
        count = len(catalog.list())
        logger.info(
            "[platform.factory] catalog loaded: %d models", count,
        )
        if count == 0:
            logger.warning(
                "[platform.factory] catalog empty — "
                "check llm_providers.yaml / API keys",
            )
        return catalog
    except Exception as exc:
        logger.exception(
            "[platform.factory] catalog build failed: %s", exc,
        )
        return None


def _build_domain_registry() -> Any:
    try:
        from backend.agent.tools.domain import (
            build_default_domain_registry,
        )
        return build_default_domain_registry()
    except Exception as exc:
        logger.exception(
            "[platform.factory] domain registry failed: %s", exc,
        )
        return None


_PLATFORM_SINGLETON = None


def _build_platform() -> Any:
    """Lazy 构造真 CodingPlatform（全局单例，REST 和 WS 共用）。"""
    global _PLATFORM_SINGLETON
    if _PLATFORM_SINGLETON is not None:
        return _PLATFORM_SINGLETON
    _PLATFORM_SINGLETON = _build_platform_impl()
    return _PLATFORM_SINGLETON


def _build_platform_impl() -> Any:
    """原构造逻辑。"""
    from backend.platform import CodingPlatform, PlatformPipeline
    from backend.agent.orchestration import CodeEditOrchestrator

    gateway = None
    router = None
    orchestrator = None
    try:
        from backend.runtime.executors.runtime_dependencies import (
            get_runtime_deps,
        )
        deps = get_runtime_deps()
        gateway = deps.get("gateway")
        router = deps.get("router")
        orchestrator = deps.get("orchestrator")
    except Exception as e:
        swallow("api.platform.factory:87", e, level="warn")

    if orchestrator is None:
        orchestrator = CodeEditOrchestrator()

    batch = None
    try:
        from backend.code_intelligence.patch_executor import PatchExecutor
        from backend.code_intelligence.patch_writer import PatchWriter
        from backend.code_intelligence.patch_validator import PatchValidator
        from backend.code_intelligence.patch_backup import PatchBackup
        from backend.platform.multi_file import BatchPatchExecutor

        batch = BatchPatchExecutor(
            executor=PatchExecutor(
                writer=PatchWriter(),
                validator=PatchValidator(),
                backup=PatchBackup(),
            )
        )
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "[platform.factory] patch executor 装配失败: %s", exc,
        )

    pipeline = PlatformPipeline(
        orchestrator=orchestrator,
        approval_gate=None,
        event_bridge=None,
        memory_bridge=None,
        patch_executor=batch,
    )
    return CodingPlatform(pipeline)


def build_platform_router() -> APIRouter:
    catalog = _build_catalog()
    domains = _build_domain_registry()
    binding = PlatformBinding(
        platform_factory=_build_platform,
        model_catalog=catalog,
        domain_registry=domains,
    )
    return PlatformRouter(binding).router


__all__ = ["build_platform_router"]
