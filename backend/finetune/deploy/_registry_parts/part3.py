"""Part 3 of registry.py."""
from __future__ import annotations

def reset_adapter_registry() -> None:
    global _registry
    _registry = None

__all__ = [
    "AdapterRegistry", "get_adapter_registry", "reset_adapter_registry",
    "scan_local_adapters",
    "save_adapter_spec", "load_adapter_spec", "list_adapter_specs",
    "delete_adapter_spec", "reset_adapter_specs",
]
