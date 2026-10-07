"""Part 1 of store.py."""
from ._header import Any, BenchmarkCaseResult, BenchmarkResult, Path, _DB_DIR, _DB_PATH, annotations, json, sqlite3, time, uuid

def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                run_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                started_at REAL NOT NULL,
                finished_at REAL NOT NULL,
                score REAL NOT NULL DEFAULT 0,
                rating TEXT NOT NULL DEFAULT '',
                error TEXT NOT NULL DEFAULT '',
                by_category_json TEXT NOT NULL DEFAULT '{}',
                cases_json TEXT NOT NULL DEFAULT '[]',
                case_count INTEGER NOT NULL DEFAULT 0,
                passed_count INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_bench_prov_model
                ON benchmark_runs(provider, model, started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_bench_created
                ON benchmark_runs(started_at DESC);
        """)


def _case_to_dict(c: BenchmarkCaseResult) -> dict:
    return c.to_dict()


def _dict_to_case(d: dict) -> BenchmarkCaseResult:
    return BenchmarkCaseResult(
        case_id=d.get("case_id", ""),
        name=d.get("name", ""),
        category=d.get("category", ""),
        passed=bool(d.get("passed", False)),
        score=float(d.get("score", 0.0)),
        latency_ms=float(d.get("latency_ms", 0.0)),
        first_token_ms=float(d.get("first_token_ms", 0.0)),
        cost=float(d.get("cost", 0.0)),
        input_tokens=int(d.get("input_tokens", 0)),
        output_tokens=int(d.get("output_tokens", 0)),
        note=str(d.get("note", "")),
        evidence=str(d.get("evidence", "")),
        attempts=int(d.get("attempts", 1)),
        successes=int(d.get("successes", 1)),
        error=str(d.get("error", "")),
        extra=dict(d.get("extra") or {}),
    )


def save_benchmark_result(result: BenchmarkResult) -> str:
    """保存一次完整测试。返回 run_id。"""
    _ensure_schema()
    run_id = "bmk-" + uuid.uuid4().hex[:12]
    cases_data = [_case_to_dict(c) for c in result.cases]
    passed_count = sum(1 for c in result.cases if c.passed)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT INTO benchmark_runs("
            "run_id, provider, model, started_at, finished_at, "
            "score, rating, error, by_category_json, cases_json, "
            "case_count, passed_count) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                result.provider,
                result.model,
                float(result.started_at),
                float(result.finished_at),
                float(result.score),
                result.rating,
                result.error[:300],
                json.dumps(result.by_category, ensure_ascii=False),
                json.dumps(cases_data, ensure_ascii=False),
                len(result.cases),
                passed_count,
            ),
        )
    return run_id


def load_benchmark_result(run_id: str) -> BenchmarkResult | None:
    """按 run_id 加载完整结果。"""
    if not run_id or not run_id.strip():
        raise ValueError("run_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT run_id, provider, model, started_at, finished_at, "
            "score, rating, error, by_category_json, cases_json "
            "FROM benchmark_runs WHERE run_id = ?",
            (run_id.strip(),),
        ).fetchone()
    if row is None:
        return None
    cases = tuple(_dict_to_case(d) for d in json.loads(row[9] or "[]"))
    return BenchmarkResult(
        provider=row[1], model=row[2],
        started_at=row[3], finished_at=row[4],
        cases=cases,
        score=float(row[5]),
        rating=str(row[6]),
        by_category=dict(json.loads(row[8] or "{}")),
        error=str(row[7]),
    )


def list_benchmark_runs(
    provider: str = "",
    model: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """列出历史（不加载 cases，省带宽）。"""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    _ensure_schema()
    sql = ("SELECT run_id, provider, model, started_at, finished_at, "
           "score, rating, case_count, passed_count, error "
           "FROM benchmark_runs")
    clauses, params = [], []
    if provider and provider.strip():
        clauses.append("provider = ?"); params.append(provider.strip())
    if model and model.strip():
        clauses.append("model = ?"); params.append(model.strip())
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY started_at DESC, rowid DESC LIMIT ?"
    params.append(int(limit))
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {
            "run_id": r[0], "provider": r[1], "model": r[2],
            "started_at": r[3], "finished_at": r[4],
            "score": r[5], "rating": r[6],
            "case_count": r[7], "passed_count": r[8],
            "error": r[9],
        }
        for r in rows
    ]


def latest_benchmark_for(provider: str, model: str) -> BenchmarkResult | None:
    """取某模型最新一次结果。"""
    if not provider or not provider.strip():
        raise ValueError("provider required")
    if not model or not model.strip():
        raise ValueError("model required")
    rows = list_benchmark_runs(provider=provider, model=model, limit=1)
    if not rows:
        return None
    return load_benchmark_result(rows[0]["run_id"])


def delete_benchmark_run(run_id: str) -> bool:
    if not run_id or not run_id.strip():
        raise ValueError("run_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM benchmark_runs WHERE run_id = ?",
            (run_id.strip(),),
        )
        return cur.rowcount > 0


def reset_benchmark_runs() -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM benchmark_runs")

