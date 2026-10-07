"""Mixin 2 of BenchmarkRouter."""
from __future__ import annotations
from ..compare import (build_compare_table, render_compare_markdown, render_compare_text,)  # noqa: F401
from fastapi.responses import (JSONResponse,)  # noqa: F401
from ..report import (render_text,)  # noqa: F401
from ..resolver import (build_runner_for,)  # noqa: F401
from ..store import (load_benchmark_result, save_benchmark_result,)  # noqa: F401
from typing import (Any, Dict,)  # noqa: F401
class _Mixin2:
    async def run_batch(self, payload: Dict[str, Any]) -> JSONResponse:
        """批量跑多个 (provider, model)。"""
        try:
            targets = payload.get("targets") or []
            if not isinstance(targets, list) or not targets:
                raise ValueError("targets must be non-empty list")
            case_timeout = float(payload.get("case_timeout_sec", 60.0))
            total_timeout = float(payload.get("total_timeout_sec", 600.0))

            results: list[dict] = []
            from .resolver import build_runner_for
            for t in targets:
                if not isinstance(t, dict):
                    continue
                p_name = str(t.get("provider", "")).strip()
                m_name = str(t.get("model", "")).strip()
                if not p_name or not m_name:
                    results.append({
                        "provider": p_name, "model": m_name,
                        "error": "provider/model required",
                    })
                    continue
                try:
                    runner = build_runner_for(
                        p_name, m_name,
                        case_timeout_sec=case_timeout,
                        total_timeout_sec=total_timeout,
                    )
                    r = await runner.run_all(p_name, m_name)
                    run_id = save_benchmark_result(r)
                    results.append({
                        "provider": p_name, "model": m_name,
                        "run_id": run_id,
                        "score": r.score, "rating": r.rating,
                        "elapsed_sec": r.elapsed_sec,
                        "by_category": r.by_category,
                        "passed": sum(1 for c in r.cases if c.passed),
                        "total": len(r.cases),
                        "error": r.error,
                    })
                except Exception as e:
                    results.append({
                        "provider": p_name, "model": m_name,
                        "error": f"{type(e).__name__}: {e}",
                    })
            return self._ok({"results": results, "count": len(results)})
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def compare(self, payload: Dict[str, Any]) -> JSONResponse:
        """按 run_ids 生成对比（JSON 结构化 + 文本 + markdown）。"""
        try:
            run_ids = payload.get("run_ids") or []
            if not isinstance(run_ids, list) or len(run_ids) < 2:
                raise ValueError("run_ids must contain >= 2 ids")
            results = []
            for rid in run_ids:
                r = load_benchmark_result(str(rid).strip())
                if r is None:
                    raise ValueError(f"run not found: {rid}")
                results.append(r)
            return self._ok({
                "table": build_compare_table(results),
                "report_text": render_compare_text(results),
                "report_markdown": render_compare_markdown(results),
            })
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def run_report_txt(self, run_id: str):
        """下载单次报告 .txt（attachment）。"""
        from fastapi.responses import PlainTextResponse
        try:
            r = load_benchmark_result(run_id)
            if r is None:
                return self._notfound("run not found: " + run_id)
            fname = f"benchmark-{r.provider}-{r.model}-{run_id}.txt"
            return PlainTextResponse(
                content=render_text(r),
                headers={"Content-Disposition": f'attachment; filename="{fname}"'},
            )
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def compare_report_txt(self, payload: Dict[str, Any]):
        """下载对比报告 .md（attachment）。"""
        from fastapi.responses import PlainTextResponse
        try:
            run_ids = payload.get("run_ids") or []
            fmt = str(payload.get("format", "markdown")).strip().lower()
            if not isinstance(run_ids, list) or len(run_ids) < 2:
                raise ValueError("run_ids must contain >= 2 ids")
            results = []
            for rid in run_ids:
                r = load_benchmark_result(str(rid).strip())
                if r is None:
                    raise ValueError(f"run not found: {rid}")
                results.append(r)
            if fmt == "text":
                content = render_compare_text(results)
                ext = "txt"
            else:
                content = render_compare_markdown(results)
                ext = "md"
            fname = f"benchmark-compare-{len(results)}models.{ext}"
            return PlainTextResponse(
                content=content,
                headers={"Content-Disposition": f'attachment; filename="{fname}"'},
            )
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    def _ok(self, data: Any) -> JSONResponse:
        return JSONResponse(status_code=200,
                            content={"ok": True, "data": data})

    def _bad(self, msg: str) -> JSONResponse:
        return JSONResponse(status_code=400, content={
            "ok": False, "error": {"code": "BAD_REQUEST", "message": msg}})

    def _notfound(self, msg: str) -> JSONResponse:
        return JSONResponse(status_code=404, content={
            "ok": False, "error": {"code": "NOT_FOUND", "message": msg}})

    def _err(self, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={
            "ok": False, "error": {
                "code": "INTERNAL",
                "message": f"{type(exc).__name__}: {exc}"}})

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION,
                "prefix": self.PREFIX, "ready": self.ready()}
