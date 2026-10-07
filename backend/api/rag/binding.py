"""RagBinding: HTTP adapter over RagService（全 async）。"""
from __future__ import annotations

from typing import Any, Dict


class RagBinding:
    VERSION = "1.1"
    PREFIX = "/api/rag"

    def _svc(self):
        from backend.rag.service import get_rag_service
        return get_rag_service()

    async def status(self) -> Dict[str, Any]:
        return await self._svc().status()

    async def count(self) -> int:
        return self._svc().count()

    async def index_dataset(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        path = str(payload.get("dataset_path", "") or "").strip()
        if not path:
            raise ValueError("dataset_path required")
        ds_id = str(payload.get("dataset_id", "") or "").strip()
        return await self._svc().index_dataset(path, dataset_id=ds_id)

    async def index_texts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        texts = payload.get("texts") or []
        if not isinstance(texts, list) or not texts:
            raise ValueError("texts required (list)")
        source = str(payload.get("source", "inline"))
        return await self._svc().index_texts(texts, source=source)

    async def query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        q = str(payload.get("query", "") or "").strip()
        if not q:
            raise ValueError("query required")
        top_k = int(payload.get("top_k", 5) or 5)
        use_rerank = payload.get("use_rerank", None)
        hits = await self._svc().query_dict(
            q, top_k=top_k, use_rerank=use_rerank,
        )
        return {"query": q, "count": len(hits), "hits": hits}

    async def list_finetune_datasets(self) -> Dict[str, Any]:
        """列出所有微调数据集（供 RAG 索引用）。"""
        from backend.finetune.dataset.manager import get_dataset_manager
        mgr = get_dataset_manager()
        rows = mgr.list(limit=1000)
        out = []
        for r in rows or []:
            out.append({
                "dataset_id": r.get("dataset_id", ""),
                "name": r.get("name", ""),
                "path": r.get("path", ""),
                "sample_count": int(r.get("sample_count", 0) or 0),
                "size_bytes": int(r.get("size_bytes", 0) or 0),
                "created_at": float(r.get("created_at", 0) or 0),
            })
        return {"datasets": out, "count": len(out)}

    async def index_all_finetune_datasets(self) -> Dict[str, Any]:
        """一键索引所有微调数据集（幂等：chunk_id 确定性 upsert）。

        返回每数据集的索引结果 + 汇总。
        """
        from backend.finetune.dataset.manager import get_dataset_manager
        mgr = get_dataset_manager()
        rows = mgr.list(limit=1000) or []
        svc = self._svc()

        results = []
        total_indexed = 0
        total_skipped = 0
        total_failed = 0

        for r in rows:
            ds_id = str(r.get("dataset_id", "") or "")
            path = str(r.get("path", "") or "")
            name = str(r.get("name", "") or ds_id)
            if not path:
                total_skipped += 1
                results.append({
                    "dataset_id": ds_id, "name": name,
                    "status": "skipped", "reason": "no path",
                })
                continue
            try:
                rep = await svc.index_dataset(path, dataset_id=ds_id)
                n = int(rep.get("indexed", 0) or 0)
                total_indexed += n
                results.append({
                    "dataset_id": ds_id, "name": name,
                    "status": "ok", "indexed": n,
                })
            except FileNotFoundError:
                total_skipped += 1
                results.append({
                    "dataset_id": ds_id, "name": name,
                    "status": "skipped", "reason": "file not found",
                })
            except Exception as exc:
                total_failed += 1
                results.append({
                    "dataset_id": ds_id, "name": name,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                })

        return {
            "dataset_count": len(rows),
            "total_indexed": total_indexed,
            "skipped": total_skipped,
            "failed": total_failed,
            "collection_total": self._svc().count(),
            "results": results,
        }

    async def clear(self) -> Dict[str, Any]:
        return self._svc().clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION}


__all__ = ["RagBinding"]
