from .descriptor import ModelDescriptor
from .errors import CatalogInvalid
from .reader import load


def resolve_default() -> ModelDescriptor:
    models, default_id = load()
    for m in models:
        if m.id == default_id:
            return m
    raise CatalogInvalid(
        f"default_model_id={default_id!r} not present in catalog")


def get_default_model_id() -> str:
    return resolve_default().id


def list_models() -> tuple[ModelDescriptor, ...]:
    return load()[0]
