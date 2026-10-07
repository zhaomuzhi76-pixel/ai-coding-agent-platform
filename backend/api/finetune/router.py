"""FinetuneRouter: FastAPI transport for finetune data."""
from __future__ import annotations

from typing import Any, Callable, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.finetune.binding import FinetuneBinding


class FinetuneRouter:
    VERSION = "1.0"
    PREFIX = "/api/finetune"

    def __init__(self, binding: FinetuneBinding) -> None:
        if not isinstance(binding, FinetuneBinding):
            raise TypeError("binding must FinetuneBinding")
        self.binding = binding
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/summary")(self.summary)
        self.router.get(f"{p}/recipes")(self.recipes)
        self.router.get(f"{p}/recipes/{{name}}")(self.recipe)
        self.router.get(f"{p}/runs")(self.runs)
        # ── 任务管理（L2）──
        self.router.post(f"{p}/jobs")(self.submit_job)
        self.router.get(f"{p}/jobs")(self.list_jobs)
        self.router.get(f"{p}/jobs/{{job_id}}")(self.get_job)
        self.router.get(f"{p}/jobs/{{job_id}}/events")(self.get_job_events)
        self.router.post(f"{p}/jobs/{{job_id}}/cancel")(self.cancel_job)
        self.router.delete(f"{p}/jobs/{{job_id}}")(self.delete_job)
        self.router.get(f"{p}/job-states")(self.job_states)
        self.router.get(f"{p}/env")(self.check_env_report)
        # ── 数据集管理（D4-L2）──
        # 注意：validate 必须放 {dataset_id} 前
        self.router.post(f"{p}/datasets/validate")(self.validate_dataset)
        self.router.post(f"{p}/datasets")(self.upload_dataset)
        self.router.get(f"{p}/datasets")(self.list_datasets)
        self.router.get(f"{p}/datasets/stats/overview")(self.dataset_stats)
        self.router.get(f"{p}/datasets/{{dataset_id}}")(self.get_dataset)
        self.router.delete(f"{p}/datasets/{{dataset_id}}")(self.delete_dataset)
        self.router.patch(f"{p}/datasets/{{dataset_id}}")(self.update_dataset)
        self.router.get(f"{p}/datasets/{{dataset_id}}/download")(self.download_dataset)
        # ── Adapter 部署（D5-L2）──
        # 静态路径必须在动态 {adapter_id} 之前
        self.router.post(f"{p}/adapters/scan")(self.scan_adapters)
        self.router.get(f"{p}/adapters/mounted")(self.list_mounted)
        self.router.get(f"{p}/adapters")(self.list_adapters)
        self.router.get(f"{p}/adapters/{{adapter_id}}")(self.get_adapter)
        self.router.get(f"{p}/adapters/{{adapter_id}}/plan")(self.build_adapter_plan)
        self.router.post(f"{p}/adapters/{{adapter_id}}/deploy")(self.deploy_adapter)
        self.router.post(f"{p}/adapters/{{adapter_id}}/mount")(self.mount_adapter)
        self.router.delete(f"{p}/adapters/{{adapter_id}}")(self.delete_adapter)

    async def summary(self) -> JSONResponse:
        return await self._wrap(self.binding.summary)

    async def recipes(self) -> JSONResponse:
        return await self._wrap(self.binding.recipes)

    async def recipe(self, name: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.recipe(name))

    async def submit_job(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(lambda: self.binding.submit_job(payload))

    async def list_jobs(self, state: str = "", limit: int = 50) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.list_jobs(state=state, limit=limit)
        )

    async def get_job(self, job_id: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.get_job(job_id))

    async def get_job_events(self, job_id: str, limit: int = 500) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.get_job_events(job_id, limit=limit)
        )

    async def cancel_job(self, job_id: str) -> JSONResponse:
        return await self._wrap_async(
            lambda: self.binding.cancel_job(job_id)
        )

    async def delete_job(self, job_id: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.delete_job(job_id))

    async def upload_dataset(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(lambda: self.binding.upload_dataset(payload))

    async def validate_dataset(self, payload: Dict[str, Any]) -> JSONResponse:
        return await self._wrap(lambda: self.binding.validate_dataset(payload))

    async def list_datasets(self, limit: int = 100) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.list_datasets(limit=limit)
        )

    async def get_dataset(self, dataset_id: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.get_dataset(dataset_id))

    async def delete_dataset(self, dataset_id: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.delete_dataset(dataset_id))
    async def update_dataset(
        self, dataset_id: str, payload: Dict[str, Any],
    ) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.update_dataset(dataset_id, payload)
        )


    async def list_adapters(self, limit: int = 100) -> JSONResponse:
        return await self._wrap(lambda: self.binding.list_adapters(limit=limit))

    async def scan_adapters(self) -> JSONResponse:
        return await self._wrap(self.binding.scan_adapters)

    async def get_adapter(self, adapter_id: str) -> JSONResponse:
        return await self._wrap(lambda: self.binding.get_adapter(adapter_id))

    async def build_adapter_plan(self, adapter_id: str) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.build_adapter_plan(adapter_id)
        )

    async def deploy_adapter(
        self, adapter_id: str, wait: bool = True,
    ) -> JSONResponse:
        return await self._wrap_async(
            lambda: self.binding.deploy_adapter(adapter_id, wait=wait)
        )

    async def mount_adapter(self, adapter_id: str) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.mount_adapter(adapter_id)
        )

    async def list_mounted(self) -> JSONResponse:
        return await self._wrap(self.binding.list_mounted)

    async def delete_adapter(self, adapter_id: str) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.delete_adapter(adapter_id)
        )

    async def download_dataset(self, dataset_id: str) -> JSONResponse:
        return await self._wrap(
            lambda: self.binding.download_dataset(dataset_id)
        )

    async def dataset_stats(self) -> JSONResponse:
        return await self._wrap(self.binding.dataset_stats)

    async def check_env_report(self) -> JSONResponse:
        return await self._wrap(self.binding.check_env_report)

    async def job_states(self) -> JSONResponse:
        return await self._wrap(self.binding.job_states)

    async def runs(self) -> JSONResponse:
        return await self._wrap(self.binding.runs)

    async def _wrap(
        self, fn: Callable[[], Any],
    ) -> JSONResponse:
        try:
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": fn()},
            )
        except KeyError as exc:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": {
                    "code": "NOT_FOUND", "message": str(exc)}},
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": {
                    "code": "INTERNAL",
                    "message": f"{type(exc).__name__}: {exc}"}},
            )

    async def _wrap_async(
        self, fn: Callable[[], Any],
    ) -> JSONResponse:
        """与 _wrap 平行：await fn() 后再包装。"""
        try:
            result = await fn()
            return JSONResponse(
                status_code=200,
                content={"ok": True, "data": result},
            )
        except KeyError as exc:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "error": {
                    "code": "NOT_FOUND", "message": str(exc)}},
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": {
                    "code": "INTERNAL",
                    "message": f"{type(exc).__name__}: {exc}"}},
            )

    def ready(self) -> bool:
        return self.binding.ready()

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["FinetuneRouter"]
