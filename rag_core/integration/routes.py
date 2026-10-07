# 职责：RAG 知识库路由（对齐 UI 面板），供主后端 app 挂载
import threading
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from .bridge import get_bridge

router = APIRouter()

class ConfigUpdate(BaseModel):
    vector_model: str = "qwen3-embedding:8b"
    rerank_model: str = "dengcao/Qwen3-Reranker-4B:Q5_K_M"
    enable_rerank: bool = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    collection: str = "中医"

class DeleteRequest(BaseModel):
    collection: str
    chunk_ids: List[str]

@router.get("/config")
async def get_config():
    return get_bridge().config.get_config()

@router.post("/config")
async def update_config(req: ConfigUpdate):
    cfg = get_bridge().update_config(req.model_dump())
    return {"status": "success", "config": cfg}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    b = get_bridge()
    task_id = b.task_mgr.create_task(file.filename)
    # 主后端同进程内异步执行，不阻塞事件循环
    threading.Thread(
        target=b.get_ingestion().run,
        args=(task_id, content, file.filename),
        daemon=True
    ).start()
    return {"task_id": task_id, "filename": file.filename}

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    t = get_bridge().task_mgr.tasks.get(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": t.task_id, "state": t.state.value,
            "progress": t.progress, "error_msg": t.error_msg}

@router.post("/search")
async def search(req: SearchRequest):
    b = get_bridge()
    enable = b.config.get_config()["enable_rerank"]
    chunks = b.get_search().search(req.query, req.top_k, req.collection, enable)
    return [{"chunk_id": c.chunk_id, "text": c.text,
             "metadata": c.metadata} for c in chunks]

@router.get("/stats/{collection}")
async def get_stats(collection: str):
    return get_bridge().store.get_stats(collection)

@router.post("/delete")
async def delete_chunks(req: DeleteRequest):
    n = get_bridge().store.delete(req.collection, req.chunk_ids)
    return {"deleted_count": n}

@router.get("/health")
async def health():
    return {"status": "ok", "service": "rag_core", "mode": "embedded"}
