"""静态图片路由：把 data/images/ 暴露为 HTTP /data/images/*。

职责：
  - GET /data/images/<kb>/<filename> → 返回 PNG/JPG
  - 仅允许 data/images 下的文件（防路径穿越）
不做：
  - 不做权限（内网用）
  - 不做缩略图（后续可加）
"""
from __future__ import annotations
import os
from typing import Any

ROOT = os.path.abspath("data/images")


def register_images_routes(router: Any) -> None:
    """挂到 FastAPI router。"""
    from fastapi.responses import FileResponse
    from fastapi import HTTPException

    @router.get("/data/images/{full_path:path}")
    async def _get_image(full_path: str):
        # 防路径穿越
        if ".." in full_path or full_path.startswith("/"):
            raise HTTPException(400, "invalid path")
        if not full_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            raise HTTPException(400, "unsupported ext")
        full = os.path.join(ROOT, full_path)
        # 二次校验：必须在 ROOT 下
        if not os.path.abspath(full).startswith(os.path.abspath(ROOT)):
            raise HTTPException(403, "forbidden")
        if not os.path.isfile(full):
            raise HTTPException(404, f"not found: {full_path}")
        media = "image/png"
        if full_path.lower().endswith((".jpg", ".jpeg")):
            media = "image/jpeg"
        elif full_path.lower().endswith(".webp"):
            media = "image/webp"
        return FileResponse(full, media_type=media)

__all__ = ["register_images_routes", "ROOT"]
