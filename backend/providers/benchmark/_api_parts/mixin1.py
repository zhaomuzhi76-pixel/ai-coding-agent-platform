"""Mixin 1 of BenchmarkRouter."""
from __future__ import annotations
from ..cases import (list_cases,)  # noqa: F401
from fastapi import (APIRouter,)  # noqa: F401
from fastapi.responses import (JSONResponse,)  # noqa: F401
from ..report import (render_text,)  # noqa: F401
from ..resolver import (build_runner_for,)  # noqa: F401
from ..store import (delete_benchmark_run, latest_benchmark_for, list_benchmark_runs, load_benchmark_result, save_benchmark_result,)  # noqa: F401
from typing import (Any, Dict,)  # noqa: F401
class _Mixin1:
    def __init__(self) -> None:
        self.router = APIRouter()
        self._register()

    def _register(self) -> None:
        p = self.PREFIX
        self.router.get(f"{p}/cases")(self.list_all_cases)
        self.router.get(f"{p}/domains")(self.list_domains)
        self.router.get(f"{p}/models")(self.list_testable_models)
        self.router.get(f"{p}/runs/{{run_id}}/summary")(self.run_summary)
        self.router.get(f"{p}/runs/{{run_id}}/download")(self.run_download)
        self.router.post(f"{p}/run")(self.run_benchmark)
        self.router.get(f"{p}/runs")(self.list_runs)
        self.router.get(f"{p}/runs/{{run_id}}/report")(self.run_report)
        self.router.get(f"{p}/runs/{{run_id}}")(self.run_detail)
        self.router.get(f"{p}/latest")(self.latest_for)
        self.router.delete(f"{p}/runs/{{run_id}}")(self.delete_run)
        self.router.post(f"{p}/run-batch")(self.run_batch)
        self.router.post(f"{p}/compare")(self.compare)
        self.router.get(f"{p}/runs/{{run_id}}/report.txt")(self.run_report_txt)
        self.router.post(f"{p}/compare/report.txt")(self.compare_report_txt)

    async def list_all_cases(self) -> JSONResponse:
        try:
            cases = [c.to_dict() for c in list_cases()]
            return self._ok({"cases": cases, "count": len(cases)})
        except Exception as exc:
            return self._err(exc)

    async def list_domains(self) -> JSONResponse:
        """能力领域清单"""
        try:
            from ..domains import domain_list
            return self._ok({"domains": domain_list()})
        except Exception as exc:
            return self._err(exc)

    async def run_summary(self, run_id: str) -> JSONResponse:
        """单模型能力总结"""
        try:
            from ..store import load_benchmark_result
            from ..summarize import summarize_result
            run = load_benchmark_result(run_id)
            if not run:
                return self._notfound(f"run not found: {run_id}")
            data = run.to_dict() if hasattr(run, "to_dict") else run
            return self._ok(summarize_result(data))
        except Exception as exc:
            return self._err(exc)

    async def run_download(self, run_id: str,
                            format: str = "json") -> JSONResponse:
        """下载报告：json / csv / md"""
        try:
            from ..store import load_benchmark_result
            from .download import to_json, to_csv, to_markdown
            run = load_benchmark_result(run_id)
            if not run:
                return self._notfound(f"run not found: {run_id}")
            data = run.to_dict() if hasattr(run, "to_dict") else run
            fmt = (format or "json").lower()
            if fmt == "csv":
                body = to_csv(data)
            elif fmt in ("md", "markdown"):
                body = to_markdown(data)
            else:
                body = to_json(data)
            return self._ok({"format": fmt, "content": body})
        except Exception as exc:
            return self._err(exc)

    async def list_testable_models(self) -> JSONResponse:
        """可测模型 —— 从 Model Registry 读（已验证 + chat 过滤）"""
        try:
            from .testable import list_testable_from_registry
            out = list_testable_from_registry()
            return self._ok({"models": out, "count": len(out)})
        except Exception as exc:
            return self._err(exc)


    async def run_benchmark(self, payload: Dict[str, Any]) -> JSONResponse:
        try:
            provider = str(payload.get("provider", "")).strip()
            model = str(payload.get("model", "")).strip()
            if not provider or not model:
                raise ValueError("provider and model required")
            case_timeout = float(payload.get("case_timeout_sec", 60.0))
            total_timeout = float(payload.get("total_timeout_sec", 600.0))

            runner = build_runner_for(
                provider, model,
                case_timeout_sec=case_timeout,
                total_timeout_sec=total_timeout,
            )
            result = await runner.run_all(provider, model)
            run_id = save_benchmark_result(result)
            return self._ok({
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "score": result.score,
                "rating": result.rating,
                "elapsed_sec": result.elapsed_sec,
                "by_category": result.by_category,
                "passed": sum(1 for c in result.cases if c.passed),
                "total": len(result.cases),
                "error": result.error,
            })
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def list_runs(self, provider: str = "", model: str = "",
                        limit: int = 20) -> JSONResponse:
        try:
            rows = list_benchmark_runs(
                provider=provider, model=model, limit=int(limit),
            )
            return self._ok({"runs": rows, "count": len(rows)})
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def run_detail(self, run_id: str) -> JSONResponse:
        try:
            r = load_benchmark_result(run_id)
            if r is None:
                return self._notfound("run not found: " + run_id)
            return self._ok(r.to_dict())
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def run_report(self, run_id: str) -> JSONResponse:
        try:
            r = load_benchmark_result(run_id)
            if r is None:
                return self._notfound("run not found: " + run_id)
            return self._ok({
                "run_id": run_id,
                "report": render_text(r),
            })
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def latest_for(self, provider: str = "",
                         model: str = "") -> JSONResponse:
        try:
            if not provider.strip() or not model.strip():
                raise ValueError("provider and model required")
            r = latest_benchmark_for(provider, model)
            if r is None:
                return self._ok({"result": None})
            return self._ok({"result": r.to_dict()})
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)

    async def delete_run(self, run_id: str) -> JSONResponse:
        try:
            ok = delete_benchmark_run(run_id)
            return self._ok({"deleted": bool(ok)})
        except ValueError as exc:
            return self._bad(str(exc))
        except Exception as exc:
            return self._err(exc)
