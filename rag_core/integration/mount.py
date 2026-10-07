# 职责：把 RAG 路由幂等挂载到任意 FastAPI app
from fastapi import FastAPI

MOUNT_PATH = "/api/rag/kb"
_STATE_KEY = "rag_embedded_mounted"

def mount_rag(app: FastAPI, mount_path: str = MOUNT_PATH) -> bool:
    """幂等挂载：已挂载返回 False，新挂载返回 True。

    使用 app.state 作为幂等锚点，避免 FastAPI 版本差异导致 routes 检测失效。
    """
    if getattr(app.state, _STATE_KEY, False):
        return False
    from .routes import router
    app.include_router(router, prefix=mount_path, tags=["rag-embedded"])
    setattr(app.state, _STATE_KEY, True)
    return True
