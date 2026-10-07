from __future__ import annotations

# ── Worker 进程 guard：禁止在 worker 里触发完整 bootstrap ──
import os as _os
_WORKER_GUARD = _os.environ.get("LOCO_WORKER_ACTIVE") == "1"

import logging
from pathlib import Path

from backend.assembly import AssemblyRuntimeFactory
from backend.assembly.application_bootstrap_composition_factory import (
    ApplicationBootstrapCompositionFactory,
)
from backend.assembly.startup_module import (
    ApplicationStartupModule,
)
from backend.config.settings import settings
from backend.system.bootstrap.application_startup import (
    SystemApplicationStartupBootstrapFactory,
    SystemStartupAssemblyFactory,
)
from backend.system.composition.system_factory import (
    SystemFactory,
)
from backend.system.integration.runtime import (
    SystemIntegrationRuntime,
)
from backend.system.integration.runtime_factory import (
    SystemIntegrationRuntimeFactory,
)
from backend.rag.governance.bootstrap_hook import (
    install_rag_governance,
    uninstall_rag_governance,
)

logger = logging.getLogger(__name__)

_runtime: SystemIntegrationRuntime | None = None
_startup_module: ApplicationStartupModule | None = None
_system_bootstrap = None


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(
            logging,
            settings.LOG_LEVEL.upper(),
            logging.INFO,
        ),
        format=(
            "%(asctime)s - %(name)s - "
            "%(levelname)s - %(message)s"
        ),
    )


def bootstrap(
    startup_module: ApplicationStartupModule | None = None,
    workspace_root: str | None = None,
):
    if _WORKER_GUARD:
        # worker 内不需要完整装配，只返回最小状态
        return None
    global _runtime
    global _startup_module
    global _system_bootstrap

    setup_logging()

    if is_bootstrapped():
        return _startup_module.startup

    if (
        _runtime is not None
        or _startup_module is not None
        or _system_bootstrap is not None
    ):
        shutdown()

    logger.info("系统启动入口")

    resolved_workspace_root = (
        str(
            Path(workspace_root)
            .expanduser()
            .resolve()
        )
        if workspace_root is not None
        else str(
            Path(__file__).resolve().parent
        )
    )

    if startup_module is None:
        startup_module = (
            ApplicationBootstrapCompositionFactory()
            .create(
                workspace_root=resolved_workspace_root,
            )
        )

    startup_module = (
        SystemStartupAssemblyFactory()
        .create(
            startup_module=startup_module,
        )
    )

    assembly_runtime = (
        AssemblyRuntimeFactory()
        .create(
            modules=(startup_module,),
        )
    )

    system = (
        SystemFactory()
        .create()
    )

    runtime = (
        SystemIntegrationRuntimeFactory()
        .create(
            assembly_runtime=assembly_runtime,
            system=system,
        )
    )

    coordinator = (
        SystemApplicationStartupBootstrapFactory()
        .create(
            startup_module=startup_module,
            runtime=runtime,
        )
    )

    try:
        startup = coordinator.start()

        if not coordinator.ready():
            coordinator.stop()
            raise RuntimeError(
                "system startup failed"
            )

    except Exception:
        try:
            coordinator.stop()
        except Exception:
            logger.exception(
                "system startup cleanup failed"
            )

        _runtime = None
        _startup_module = None
        _system_bootstrap = None
        raise

    _runtime = runtime
    _startup_module = startup_module
    _system_bootstrap = coordinator

    install_rag_governance()

    logger.info("系统启动完成")
    return startup


def is_bootstrapped() -> bool:
    coordinator = _system_bootstrap

    return (
        coordinator is not None
        and coordinator.ready()
        and _runtime is not None
        and _startup_module is not None
    )


def get_startup():
    if not is_bootstrapped():
        return None

    return _startup_module.startup


def get_integration_runtime():
    if not is_bootstrapped():
        return None

    return _runtime


def stop() -> None:
    shutdown()


def shutdown() -> None:
    global _runtime
    global _startup_module
    global _system_bootstrap

    uninstall_rag_governance()

    coordinator = _system_bootstrap

    _system_bootstrap = None
    _startup_module = None
    _runtime = None

    if coordinator is not None:
        coordinator.stop()


__all__ = [
    "bootstrap",
    "is_bootstrapped",
    "get_startup",
    "get_integration_runtime",
    "stop",
    "shutdown",
]
