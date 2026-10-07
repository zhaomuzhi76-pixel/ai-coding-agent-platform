"""Catalog 门面。外部只允许 import 本模块。"""
from .descriptor import ModelDescriptor
from .reader import clear_cache as _clear
from .resolver import get_default_model_id, list_models, resolve_default


def catalog_snapshot() -> dict:
    default_id = get_default_model_id()
    return {
        "defaultModelId": default_id,
        "models": [
            m.to_wire(is_default=(m.id == default_id))
            for m in list_models()
        ],
    }


def reload_catalog() -> None:
    _clear()


__all__ = [
    "ModelDescriptor", "catalog_snapshot", "get_default_model_id",
    "resolve_default", "list_models", "reload_catalog",
]
