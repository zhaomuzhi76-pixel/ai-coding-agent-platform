"""微调产出 → RAG 桥接：把微调数据入库到 RAG 向量库"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(prefix="/api/finetune", tags=["finetune-rag"])


def _adapter_dir() -> Path:
    return Path(os.path.expanduser("~/.biancheng/adapters"))


def _dataset_dir() -> Path:
    return Path(os.path.expanduser("~/.biancheng/datasets"))


def _find_dataset_path(dataset_id: str) -> str:
    """从 dataset_id 找 JSONL 路径"""
    base = _dataset_dir()
    if not base.exists():
        return ""
    for f in base.glob(f"{dataset_id}*"):
        if f.is_file() and f.suffix in (".jsonl", ".json"):
            return str(f)
        if f.is_dir():
            for sub in f.rglob("*.jsonl"):
                return str(sub)
    return ""


async def _call_rag_index(path: str, dataset_id: str,
                          tags: List[str]) -> Dict[str, Any]:
    """调用 RAG 的 index_dataset 内部服务"""
    from backend.api.rag.binding import RagBinding
    binding = RagBinding()
    payload = {
        "path": path,
        "dataset_id": dataset_id,
        "tags": tags,
        "source": "finetune",
    }
    return await binding.index_dataset(payload)


@router.get("/adapters/{adapter_id}/rag-status")
async def rag_status(adapter_id: str) -> Dict[str, Any]:
    """查询 adapter 是否已送 RAG"""
    marker = _adapter_dir() / f"{adapter_id}.rag.json"
    if marker.exists():
        try:
            return {"ok": True, "indexed": True,
                    "info": json.loads(marker.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return {"ok": True, "indexed": False}


@router.post("/adapters/{adapter_id}/to-rag")
async def to_rag(adapter_id: str,
                 payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """把 adapter 关联的数据集送 RAG"""
    # 1. 找 adapter 关联的 dataset
    dataset_id = payload.get("dataset_id", "")
    dataset_path = payload.get("dataset_path", "")

    if not dataset_path and dataset_id:
        dataset_path = _find_dataset_path(dataset_id)

    if not dataset_path:
        # 从 adapter 元数据读
        meta_path = _adapter_dir() / f"{adapter_id}.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                dataset_path = meta.get("dataset_path", "")
            except Exception:
                pass

    if not dataset_path or not Path(dataset_path).exists():
        raise HTTPException(400, f"未找到数据集: {dataset_path or dataset_id}")

    # 2. 调 RAG 入库
    rag_dataset_id = f"finetune_{adapter_id}"
    try:
        result = await _call_rag_index(
            dataset_path, rag_dataset_id,
            tags=["finetune", adapter_id, "sft"],
        )
    except Exception as e:
        raise HTTPException(500, f"RAG 入库失败: {type(e).__name__}: {e}")

    # 3. 写标记
    marker = _adapter_dir() / f"{adapter_id}.rag.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    info = {"adapter_id": adapter_id, "dataset_path": dataset_path,
            "rag_dataset_id": rag_dataset_id, "indexed_at": __import__("time").time()}
    marker.write_text(json.dumps(info, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    return {"ok": True, "adapter_id": adapter_id, "result": result, "info": info}


@router.post("/datasets/{dataset_id}/to-rag")
async def dataset_to_rag(dataset_id: str,
                         payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """把数据集直接送 RAG（不依赖 adapter）"""
    path = _find_dataset_path(dataset_id)
    if not path:
        raise HTTPException(404, f"数据集不存在: {dataset_id}")
    rag_id = payload.get("rag_dataset_id", f"finetune_ds_{dataset_id}")
    tags = payload.get("tags", ["finetune", "raw_dataset"])
    try:
        result = await _call_rag_index(path, rag_id, tags)
    except Exception as e:
        raise HTTPException(500, f"RAG 入库失败: {e}")
    return {"ok": True, "dataset_id": dataset_id, "result": result}


@router.get("/rag-datasets")
async def list_rag_datasets() -> Dict[str, Any]:
    """列出所有从微调送 RAG 的数据集"""
    base = _adapter_dir()
    out = []
    if base.exists():
        for f in base.glob("*.rag.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                out.append(d)
            except Exception:
                pass
    return {"ok": True, "datasets": out, "count": len(out)}
