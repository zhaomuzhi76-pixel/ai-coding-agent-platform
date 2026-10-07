"""Part 1 of storage.py."""
from ._header import Any, DATASET_DIR_NAME, DATASET_ID_PREFIX, DatasetFormat, DatasetSpec, Path, _DATASET_DIR, _DB_DIR, _DB_PATH, annotations, json, sqlite3, time

def ensure_dataset_dir() -> Path:
    _DATASET_DIR.mkdir(parents=True, exist_ok=True)
    return _DATASET_DIR


def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS finetune_datasets (
                dataset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'jsonl',
                description TEXT NOT NULL DEFAULT '',
                sample_count INTEGER NOT NULL DEFAULT 0,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]'
            );
            CREATE INDEX IF NOT EXISTS idx_ft_datasets_created
                ON finetune_datasets(created_at DESC);
        """)


def dataset_file_path(dataset_id: str) -> Path:
    """按 dataset_id 生成规范文件路径。"""
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError("dataset_id required")
    did = dataset_id.strip()
    if not did.startswith(DATASET_ID_PREFIX):
        raise ValueError(f"dataset_id must start with {DATASET_ID_PREFIX!r}")
    # 防目录穿越：只允许字母数字下划线连字符
    if not all(c.isalnum() or c in "-_" for c in did):
        raise ValueError("dataset_id contains invalid characters")
    return ensure_dataset_dir() / f"{did}.jsonl"


def dataset_file_exists(dataset_id: str) -> bool:
    return dataset_file_path(dataset_id).is_file()


def save_dataset_file(dataset_id: str, content: bytes) -> str:
    """写文件。返回绝对路径。"""
    if not isinstance(content, (bytes, bytearray)):
        raise TypeError("content must bytes")
    path = dataset_file_path(dataset_id)
    path.write_bytes(bytes(content))
    return str(path)


def read_dataset_file(dataset_id: str) -> bytes:
    path = dataset_file_path(dataset_id)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path.read_bytes()


def delete_dataset_file(dataset_id: str) -> bool:
    path = dataset_file_path(dataset_id)
    if not path.is_file():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def save_dataset_metadata(spec: DatasetSpec) -> None:
    if not isinstance(spec, DatasetSpec):
        raise TypeError("spec must DatasetSpec")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO finetune_datasets("
            "dataset_id, name, path, format, description, "
            "sample_count, size_bytes, created_at, tags_json) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                spec.dataset_id,
                spec.name,
                spec.path,
                spec.format.value,
                spec.description,
                int(spec.sample_count),
                int(spec.size_bytes),
                float(spec.created_at),
                json.dumps(list(spec.tags), ensure_ascii=False),
            ),
        )


def update_dataset_metadata(
    dataset_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    tags: list | None = None,
) -> DatasetSpec | None:
    """更新 dataset metadata（name/description/tags）。找不到返回 None。"""
    if not dataset_id or not dataset_id.strip():
        raise ValueError("dataset_id required")
    spec = load_dataset_metadata(dataset_id.strip())
    if spec is None:
        return None
    import dataclasses as _dc
    updated = _dc.replace(
        spec,
        name=(name if name is not None else spec.name),
        description=(description if description is not None else spec.description),
        tags=(tuple(str(t) for t in tags) if tags is not None else spec.tags),
    )
    save_dataset_metadata(updated)
    return updated


def load_dataset_metadata(dataset_id: str) -> DatasetSpec | None:
    if not dataset_id or not dataset_id.strip():
        raise ValueError("dataset_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT dataset_id, name, path, format, description, "
            "sample_count, size_bytes, created_at, tags_json "
            "FROM finetune_datasets WHERE dataset_id = ?",
            (dataset_id.strip(),),
        ).fetchone()
    if row is None:
        return None
    try:
        fmt = DatasetFormat(row[3])
    except ValueError:
        fmt = DatasetFormat.JSONL
    return DatasetSpec(
        dataset_id=row[0],
        name=row[1],
        path=row[2],
        format=fmt,
        description=row[4],
        sample_count=int(row[5]),
        size_bytes=int(row[6]),
        created_at=float(row[7]),
        tags=tuple(str(t) for t in json.loads(row[8] or "[]")),
    )


def list_dataset_metadata(limit: int = 100) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT dataset_id, name, path, format, description, "
            "sample_count, size_bytes, created_at, tags_json "
            "FROM finetune_datasets "
            "ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append({
            "dataset_id": row[0],
            "name": row[1],
            "path": row[2],
            "format": row[3],
            "description": row[4],
            "sample_count": int(row[5]),
            "size_bytes": int(row[6]),
            "created_at": float(row[7]),
            "tags": list(json.loads(row[8] or "[]")),
        })
    return out


def delete_dataset_metadata(dataset_id: str) -> bool:
    if not dataset_id or not dataset_id.strip():
        raise ValueError("dataset_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM finetune_datasets WHERE dataset_id = ?",
            (dataset_id.strip(),),
        )
        return cur.rowcount > 0


def reset_dataset_metadata() -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM finetune_datasets")

