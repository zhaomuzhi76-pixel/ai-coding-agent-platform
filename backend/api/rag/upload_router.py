"""RAG 上传 API（multipart）。职责：接收文件 → 落临时文件 → 提交异步 job。
立即返回 job_id；前端轮询 GET /api/rag/ingest/jobs/{id} 拿进度。
不做业务、不持状态。**不能**加 from __future__ import annotations。
"""
import os
import tempfile
from typing import Any, Callable

from fastapi import APIRouter, File, Form, UploadFile

PREFIX = "/api/rag/ingest"
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1GB
ALLOWED_EXT = {
    ".pdf", ".md", ".markdown", ".txt", ".log",
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff",
    ".docx", ".xlsx", ".pptx", ".html", ".htm",
}


def _check_ext(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(
            f"不支持的扩展名 {ext!r}，仅支持 {sorted(ALLOWED_EXT)}")
    return ext


def register_upload_routes(router: Any,
                            get_worker: Callable[[], Any]) -> None:
    @router.post(f"{PREFIX}/upload")
    async def _upload(
        file: UploadFile = File(...),
        kb: str = Form("general"),
        lang: str = Form(""),
        dry_run: bool = Form(False),
    ) -> dict:
        try:
            filename = file.filename or "unnamed"
            ext = _check_ext(filename)

            # 流式落临时文件（防 736MB 全读内存）
            fd, tmp_path = tempfile.mkstemp(suffix=ext, prefix="ragup_")
            total = 0
            try:
                with os.fdopen(fd, "wb") as out:
                    while True:
                        chunk = await file.read(1024 * 1024)  # 1MB
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_UPLOAD_BYTES:
                            raise ValueError(
                                f"file too large (> {MAX_UPLOAD_BYTES})")
                        out.write(chunk)
            except Exception:
                try: os.unlink(tmp_path)
                except OSError: pass
                raise

            w = get_worker()
            job = w.submit_file(
                file_path=tmp_path, filename=filename, kb=kb,
                lang=lang, size_bytes=total, dry_run=dry_run,
                cleanup=True)
            return {"ok": True, "data": {
                "job_id": job.job_id, "filename": filename,
                "kb": kb, "size_bytes": total,
                "status": job.status.value,
                "poll_url": f"{PREFIX}/jobs/{job.job_id}",
            }}
        except Exception as e:
            return {"ok": False, "error": {
                "code": type(e).__name__, "message": str(e)}}


__all__ = ["register_upload_routes", "PREFIX",
           "MAX_UPLOAD_BYTES", "ALLOWED_EXT", "_check_ext"]
