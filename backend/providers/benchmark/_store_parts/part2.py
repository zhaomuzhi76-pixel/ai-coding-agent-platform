"""Part 2 of store.py."""
from ._header import Any, BenchmarkCaseResult, BenchmarkResult, Path, _DB_DIR, _DB_PATH, annotations, json, sqlite3, time, uuid

class BenchmarkStore:
    """面向对象封装（可选）。"""

    VERSION = "1.0"

    def save(self, result: BenchmarkResult) -> str:
        return save_benchmark_result(result)

    def load(self, run_id: str) -> BenchmarkResult | None:
        return load_benchmark_result(run_id)

    def list(self, provider: str = "", model: str = "",
             limit: int = 20) -> list[dict]:
        return list_benchmark_runs(provider=provider, model=model, limit=limit)

    def latest(self, provider: str, model: str) -> BenchmarkResult | None:
        return latest_benchmark_for(provider, model)

    def delete(self, run_id: str) -> bool:
        return delete_benchmark_run(run_id)

    def reset(self) -> None:
        reset_benchmark_runs()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION}

