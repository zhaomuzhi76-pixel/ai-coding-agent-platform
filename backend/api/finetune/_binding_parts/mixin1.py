"""Mixin 1 of FinetuneBinding."""
from __future__ import annotations
from .part1 import (Any, Dict, List, RECIPES, all_states, create_job_spec, get_dataset_manager, get_job_manager, get_recipe, list_recipes,)  # noqa: F401
class _Mixin1:
    def __init__(self) -> None:
        # runs 注册表：内存级，未来接持久层
        self._runs: List[Dict[str, Any]] = []

    def recipes(self) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for name in list_recipes():
            r = RECIPES[name]
            out.append({
                "name": r.name,
                "description": r.description,
            })
        return {"recipes": out, "count": len(out)}

    def recipe(self, name: str) -> Dict[str, Any]:
        r = get_recipe(name)
        cfg = r.create("Qwen/Qwen2.5-7B-Instruct")
        return {
            "name": r.name,
            "description": r.description,
            "config": cfg.to_dict(),
        }

    def runs(self) -> Dict[str, Any]:
        return {"runs": list(self._runs), "count": len(self._runs)}

    def summary(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for r in self._runs:
            s = str(r.get("status", "unknown"))
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "recipes": len(RECIPES),
            "runs": len(self._runs),
            "statuses": statuses,
        }

    def submit_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """提交一次训练任务。"""
        recipe = str(payload.get("recipe_name", "")).strip()
        base_model = str(payload.get("base_model", "")).strip()
        dataset_path = str(payload.get("dataset_path", "")).strip()
        output_dir = str(payload.get("output_dir", "")).strip()
        if not recipe:
            raise ValueError("recipe_name required")
        if not base_model:
            raise ValueError("base_model required")
        if not dataset_path:
            raise ValueError("dataset_path required")
        if not output_dir:
            # 默认：~/.biancheng/finetune/<job_name>
            from pathlib import Path as _P
            default_name = str(payload.get("job_name", "") or recipe).strip()
            output_dir = str(_P.home() / ".biancheng" / "finetune" / default_name)

        # 校验 recipe 存在
        get_recipe(recipe)

        spec = create_job_spec(
            recipe_name=recipe,
            base_model=base_model,
            dataset_path=dataset_path,
            output_dir=output_dir,
            job_name=str(payload.get("job_name", "")),
            description=str(payload.get("description", "")),
            tags=list(payload.get("tags") or []),
            num_epochs=int(payload.get("num_epochs", 0) or 0),
            batch_size=int(payload.get("batch_size", 0) or 0),
            learning_rate=float(payload.get("learning_rate", 0.0) or 0.0),
            max_seq_len=int(payload.get("max_seq_len", 0) or 0),
        )
        mgr = get_job_manager()
        # 在 async route 里调用（有 running loop）→ 自动 spawn 后台 task
        record = mgr.submit(spec)
        return record.to_dict()

    def list_jobs(self, state: str = "", limit: int = 50) -> Dict[str, Any]:
        mgr = get_job_manager()
        rows = mgr.list(state=state, limit=int(limit))
        return {"jobs": rows, "count": len(rows)}

    def get_job(self, job_id: str) -> Dict[str, Any]:
        if not job_id or not job_id.strip():
            raise ValueError("job_id required")
        mgr = get_job_manager()
        rec = mgr.get(job_id.strip())
        if rec is None:
            raise KeyError(f"job not found: {job_id}")
        return rec.to_dict()

    def get_job_events(self, job_id: str, limit: int = 500) -> Dict[str, Any]:
        if not job_id or not job_id.strip():
            raise ValueError("job_id required")
        mgr = get_job_manager()
        events = mgr.events(job_id.strip(), limit=int(limit))
        return {"events": events, "count": len(events)}

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        if not job_id or not job_id.strip():
            raise ValueError("job_id required")
        mgr = get_job_manager()
        ok = await mgr.cancel(job_id.strip())
        return {"cancelled": bool(ok), "job_id": job_id.strip()}

    def delete_job(self, job_id: str) -> Dict[str, Any]:
        if not job_id or not job_id.strip():
            raise ValueError("job_id required")
        from backend.finetune.job.store import delete_job_record
        ok = delete_job_record(job_id.strip())
        return {"deleted": bool(ok), "job_id": job_id.strip()}

    def job_states(self) -> Dict[str, Any]:
        return {"states": list(all_states())}

    def upload_dataset(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """上传数据集（JSON body: name + content + description + tags）。

        content 是 JSONL 文本（非 base64），前后端都直接处理文本。
        """
        name = str(payload.get("name", "")).strip()
        content = payload.get("content", "")
        description = str(payload.get("description", ""))
        tags = payload.get("tags") or []
        if not name:
            raise ValueError("name required")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content required (JSONL text)")
        # 大小限制 50MB（防滥用）
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > 50 * 1024 * 1024:
            raise ValueError("content too large (>50MB)")
        mgr = get_dataset_manager()
        spec = mgr.upload(name, content_bytes,
                          description=description,
                          tags=list(tags))
        return spec.to_dict()

    def validate_dataset(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """预校验（不落盘）。返回报告供前端先看再确认。"""
        content = payload.get("content", "")
        if not isinstance(content, str):
            raise ValueError("content required")
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > 50 * 1024 * 1024:
            raise ValueError("content too large (>50MB)")
        mgr = get_dataset_manager()
        report = mgr.validate_upload(content_bytes)
        return report.to_dict()

    def update_dataset(
        self, dataset_id: str, payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id required")
        mgr = get_dataset_manager()
        spec = mgr.update(
            dataset_id.strip(),
            name=payload.get("name"),
            description=payload.get("description"),
            tags=payload.get("tags"),
        )
        return spec.to_dict()

    def list_datasets(self, limit: int = 100) -> Dict[str, Any]:
        mgr = get_dataset_manager()
        rows = mgr.list(limit=int(limit))
        return {"datasets": rows, "count": len(rows)}

    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id required")
        mgr = get_dataset_manager()
        spec = mgr.get(dataset_id.strip())
        if spec is None:
            raise KeyError(f"dataset not found: {dataset_id}")
        return spec.to_dict()

    def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id required")
        mgr = get_dataset_manager()
        ok = mgr.delete(dataset_id.strip())
        return {"deleted": bool(ok), "dataset_id": dataset_id.strip()}
