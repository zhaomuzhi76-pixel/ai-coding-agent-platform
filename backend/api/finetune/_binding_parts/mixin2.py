"""Mixin 2 of FinetuneBinding."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Any, Dict, _check_env, build_deploy_plan, delete_adapter_spec, get_dataset_manager, is_ollama_available, list_adapter_specs, list_mounted_adapters, load_adapter_spec, mount_adapter_to_providers, scan_local_adapters,)  # noqa: F401
class _Mixin2:
    def download_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """读取数据集文件内容（供下载）。"""
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id required")
        from backend.finetune.dataset.storage import read_dataset_file
        try:
            content = read_dataset_file(dataset_id.strip())
        except FileNotFoundError:
            raise KeyError(f"dataset file not found: {dataset_id}")
        return {
            "dataset_id": dataset_id.strip(),
            "content": content.decode("utf-8", errors="replace"),
        }

    def dataset_stats(self) -> Dict[str, Any]:
        mgr = get_dataset_manager()
        return mgr.stats()

    def list_adapters(self, limit: int = 100) -> Dict[str, Any]:
        rows = list_adapter_specs(limit=int(limit))
        return {"adapters": rows, "count": len(rows)}

    def scan_adapters(self) -> Dict[str, Any]:
        found = scan_local_adapters(register=True)
        return {
            "scanned": len(found),
            "adapters": [s.to_dict() for s in found],
        }

    def get_adapter(self, adapter_id: str) -> Dict[str, Any]:
        if not adapter_id or not adapter_id.strip():
            raise ValueError("adapter_id required")
        spec = load_adapter_spec(adapter_id.strip())
        if spec is None:
            raise KeyError(f"adapter not found: {adapter_id}")
        return spec.to_dict()

    def build_adapter_plan(self, adapter_id: str) -> Dict[str, Any]:
        if not adapter_id or not adapter_id.strip():
            raise ValueError("adapter_id required")
        spec = load_adapter_spec(adapter_id.strip())
        if spec is None:
            raise KeyError(f"adapter not found: {adapter_id}")
        plan = build_deploy_plan(spec)
        return plan.to_dict()

    async def _deploy_core(self, spec) -> Dict[str, Any]:
        """核心部署（内部）：merge→GGUF→create + 成功挂载。"""
        from backend.finetune.deploy.deployer import run_merged_gguf_deploy
        result = await run_merged_gguf_deploy(spec)
        if result.get("ok"):
            try:
                from dataclasses import replace as _dc_replace
                from backend.finetune.deploy.registry import (
                    save_adapter_spec as _save,
                )
                updated = _dc_replace(
                    spec, ollama_model_name=result["model_name"])
                _save(updated)
                mount_adapter_to_providers(updated)
            except Exception as e:
                swallow("api.finetune._binding_parts.mixin2:68", e, level="warn")
        return result

    async def deploy_adapter(
        self, adapter_id: str, wait: bool = True,
    ) -> Dict[str, Any]:
        if not adapter_id or not adapter_id.strip():
            raise ValueError("adapter_id required")
        if not is_ollama_available():
            raise RuntimeError("ollama CLI not available")
        spec = load_adapter_spec(adapter_id.strip())
        if spec is None:
            raise KeyError(f"adapter not found: {adapter_id}")

        if wait:
            return await self._deploy_core(spec)

        # 异步：spawn task，立即返回 task_id
        import asyncio as _aio
        from backend.finetune.deploy.deploy_hub import get_deploy_hub
        from backend.finetune.deploy.deployer import run_merged_gguf_deploy

        hub = get_deploy_hub()
        tid = hub.create(spec.adapter_id)

        def _on_step(ev: dict) -> None:
            hub.publish(tid, ev)

        def _on_log(msg: str) -> None:
            hub.publish(tid, {"type": "log", "message": str(msg)[:300]})

        async def _runner() -> None:
            try:
                result = await run_merged_gguf_deploy(
                    spec, on_log=_on_log, on_step=_on_step)
                if result.get("ok"):
                    try:
                        from dataclasses import replace as _dc_replace
                        from backend.finetune.deploy.registry import (
                            save_adapter_spec as _save,
                        )
                        updated = _dc_replace(
                            spec, ollama_model_name=result["model_name"])
                        _save(updated)
                        mount_adapter_to_providers(updated)
                    except Exception as e:
                        swallow("api.finetune._binding_parts.mixin2:114", e, level="warn")
                hub.finish(tid, "succeeded" if result.get("ok") else "failed",
                           result)
            except Exception as exc:
                hub.publish(tid, {"type": "error", "message": str(exc)[:300]})
                hub.finish(tid, "failed", {"ok": False, "error": str(exc)})

        _aio.create_task(_runner())
        return {"task_id": tid, "adapter_id": spec.adapter_id,
                "status": "pending", "async": True}

    def mount_adapter(self, adapter_id: str) -> Dict[str, Any]:
        if not adapter_id or not adapter_id.strip():
            raise ValueError("adapter_id required")
        spec = load_adapter_spec(adapter_id.strip())
        if spec is None:
            raise KeyError(f"adapter not found: {adapter_id}")
        entry = mount_adapter_to_providers(spec)
        return entry.to_dict()

    def list_mounted(self) -> Dict[str, Any]:
        rows = list_mounted_adapters()
        return {"mounted": rows, "count": len(rows)}

    def delete_adapter(self, adapter_id: str) -> Dict[str, Any]:
        if not adapter_id or not adapter_id.strip():
            raise ValueError("adapter_id required")
        ok = delete_adapter_spec(adapter_id.strip())
        return {"deleted": bool(ok), "adapter_id": adapter_id.strip()}

    def check_env_report(self) -> Dict[str, Any]:
        return _check_env().to_dict()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }
