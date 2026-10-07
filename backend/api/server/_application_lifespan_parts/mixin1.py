"""Mixin 1 of ApplicationLifespan."""
from __future__ import annotations
from contextlib import asynccontextmanager
from .part1 import (Callable, FastAPI, FastAPIApplicationLifespanRuntimeOrchestrator, FastAPIApplicationLifespanRuntimeOrchestratorFactory, inspect,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        *,
        bootstrap: Callable | None = None,
        shutdown: Callable | None = None,
        orchestrator: (
            FastAPIApplicationLifespanRuntimeOrchestrator
            | None
        ) = None,
    ) -> None:
        if not callable(bootstrap):
            raise TypeError(
                "bootstrap callable required"
            )

        if not callable(shutdown):
            raise TypeError(
                "shutdown callable required"
            )

        self.bootstrap = bootstrap
        self.bootstrap_shutdown = shutdown
        self.orchestrator = (
            orchestrator
            or FastAPIApplicationLifespanRuntimeOrchestratorFactory().create()
        )
        self.startup = None
        self._bootstrap_shutdown_done = False

    @asynccontextmanager
    async def lifespan(
        self,
        app: FastAPI,
    ):
        self.startup = None
        self._bootstrap_shutdown_done = False

        try:
            self.startup = self.bootstrap()

            await self._invoke(
                self.orchestrator.start,
                application=app,
                startup=self.startup,
            )

            if not self.orchestrator.ready():
                raise RuntimeError(
                    "application runtime orchestrator unavailable"
                )

            # 启动时同步探测所有 provider（最多等 15 秒）
            await self._sync_health_probe()

            # 启动时发现所有 ollama 模型（自动发现，不写死）
            await self._sync_ollama_discovery()

            # 首次启动：把 yaml 里 provider 迁移到 verified 白名单
            await self._migrate_verified_from_config()

            yield

        except Exception:
            try:
                if self.orchestrator.started:
                    await self._invoke(
                        self.orchestrator.stop,
                        application=app,
                    )
            finally:
                self._shutdown_bootstrap_once()
            raise

        finally:
            try:
                if self.orchestrator.started:
                    await self._invoke(
                        self.orchestrator.stop,
                        application=app,
                    )
            finally:
                self._shutdown_bootstrap_once()
                self.startup = None

    @staticmethod
    async def _invoke(
        method,
        **kwargs,
    ) -> object:
        result = method(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    async def _sync_health_probe() -> None:
        """启动时同步探测所有 provider（最多等 15 秒）。"""
        import asyncio
        try:
            from backend.providers.health.registry import get_checker
            checker = get_checker()
            print("[startup] probing providers (max 15s)...", flush=True)
            records = await asyncio.wait_for(
                checker.check_all(), timeout=15.0,
            )
            for r in records:
                mark = "OK" if r.status == "healthy" else "FAIL"
                err = f" err={r.error}" if r.error else ""
                print(
                    f"[startup] probe {r.provider} -> {mark} "
                    f"({r.status}, {r.latency_ms:.0f}ms){err}",
                    flush=True,
                )
        except asyncio.TimeoutError:
            print("[startup] health probe timeout (15s)", flush=True)
        except Exception as exc:
            print(
                f"[startup] health probe failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

    @staticmethod
    async def _sync_ollama_discovery() -> None:
        """启动时自动发现所有 ollama 模型（最多等 10 秒）。"""
        import asyncio
        try:
            from backend.providers.discovery import (
                refresh_ollama_discovery,
            )
            print(
                "[startup] discovering ollama models (max 10s)...",
                flush=True,
            )
            cache = await asyncio.wait_for(
                refresh_ollama_discovery(), timeout=10.0,
            )
            for name, models in cache.items():
                print(
                    f"[startup] discovered {name}: "
                    f"{len(models)} chat models",
                    flush=True,
                )
        except asyncio.TimeoutError:
            print(
                "[startup] ollama discovery timeout (10s)",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[startup] ollama discovery failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

    @staticmethod
    async def _migrate_verified_from_config() -> None:
        """首次启动：yaml 里 provider 一次性进白名单。

        仅当 .verified.json 不存在时执行。
        """
        try:
            from backend.api.providers.verified_store import get_store
            from backend.providers.config import load_llm_config

            store = get_store()
            if store.path.is_file():
                print(
                    "[startup] verified store exists, skip migration",
                    flush=True,
                )
                return

            cfg = load_llm_config()
            names = [p.name for p in cfg.providers]
            added = store.migrate_from_config(names)
            print(
                f"[startup] migrated {added}/{len(names)} "
                f"providers to verified list",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[startup] verified migration failed: "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

    def _shutdown_bootstrap_once(
        self,
    ) -> None:
        if self._bootstrap_shutdown_done:
            return

        self._bootstrap_shutdown_done = True
        self.bootstrap_shutdown()
