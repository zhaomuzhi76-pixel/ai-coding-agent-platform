"""Frontend 静态服务：把 frontend/dist 挂到 /app。

契约：
    - /app/**        → 静态文件（assets/index-xxx.js 等）
    - /app/*         → SPA fallback 返回 index.html
    - 目录不存在 → 静默跳过（开发时 dist 可能未 build）

不负责：
    - API 路由（其它 router 管）
    - WS 端点（ws_* 管）
    - build（前端自己 build）
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


MOUNT_PATH = "/app"


def _find_dist() -> Path | None:
    here = Path(__file__).resolve()
    for up in range(1, 6):
        cand = here.parents[up] / "frontend" / "dist"
        if (cand / "index.html").is_file():
            return cand
    return None


def mount_frontend(app: FastAPI) -> bool:
    """挂载 /app 静态服务；成功返回 True，dist 缺失返回 False。"""
    dist = _find_dist()
    if dist is None:
        return False

    # 静态资源（assets/ 等）
    app.mount(
        MOUNT_PATH,
        StaticFiles(directory=str(dist), html=True),
        name="frontend-app",
    )

    # SPA 路由 fallback：任何 /app/xxx 未命中文件 → 返回 index.html
    index_file = dist / "index.html"

    @app.get(MOUNT_PATH + "/{full_path:path}", include_in_schema=False)
    async def _spa_fallback(full_path: str):
        target = dist / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(index_file)

    return True


__all__ = ["mount_frontend", "MOUNT_PATH"]
