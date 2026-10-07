import json
import os
from functools import lru_cache
from pathlib import Path

from .descriptor import ModelDescriptor
from .errors import CatalogInvalid, CatalogNotFound
from .schema import parse

_ENV = "LOCO_PROVIDER_CATALOG"


def _resolve_path(explicit: str | None) -> Path:
    p = (explicit
         or os.environ.get(_ENV)
         or str(Path(__file__).parents[1] / "catalog.json"))
    path = Path(p)
    if not path.exists():
        raise CatalogNotFound(f"catalog not found: {path}")
    return path


@lru_cache(maxsize=8)
def _load_cached(path_str: str) -> tuple[tuple[ModelDescriptor, ...], str]:
    raw = json.loads(Path(path_str).read_text(encoding="utf-8"))
    try:
        models, default_id = parse(raw)
    except CatalogInvalid:
        raise
    return tuple(models), default_id


def load(path: str | None = None) -> tuple[tuple[ModelDescriptor, ...], str]:
    """返回 (models, default_model_id)。除显式 path 外走 lru_cache。"""
    return _load_cached(str(_resolve_path(path)))


def clear_cache() -> None:
    _load_cached.cache_clear()
