from .descriptor import ModelDescriptor
from .errors import CatalogInvalid

_REQUIRED_TOP = {"version", "default_model_id", "models"}
_REQUIRED_MODEL = {"id", "provider", "display_name", "context_window"}


def parse(raw: dict) -> tuple[list[ModelDescriptor], str]:
    if not isinstance(raw, dict):
        raise CatalogInvalid(
            f"catalog root must be object, got {type(raw).__name__}")
    missing = _REQUIRED_TOP - raw.keys()
    if missing:
        raise CatalogInvalid(f"missing top-level keys: {sorted(missing)}")

    default_id = raw["default_model_id"]
    if not isinstance(default_id, str) or not default_id:
        raise CatalogInvalid("default_model_id must be non-empty str")

    models: list[ModelDescriptor] = []
    for i, m in enumerate(raw["models"]):
        if not isinstance(m, dict):
            raise CatalogInvalid(f"models[{i}] not an object")
        miss = _REQUIRED_MODEL - m.keys()
        if miss:
            raise CatalogInvalid(f"models[{i}] missing {sorted(miss)}")
        cw = m["context_window"]
        if not isinstance(cw, int) or cw <= 0:
            raise CatalogInvalid(
                f"models[{i}].context_window must be positive int")
        models.append(ModelDescriptor(
            id=m["id"], provider=m["provider"],
            display_name=m["display_name"], context_window=cw,
        ))

    if not models:
        raise CatalogInvalid("catalog has no models")
    return models, default_id
