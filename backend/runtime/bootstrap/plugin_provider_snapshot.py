from __future__ import annotations


def build_plugin_provider_snapshot(
    provider,
) -> dict[str, object]:
    """
    Build the observable runtime plugin-provider snapshot.

    Responsibility:
        - collect plugin-provider diagnostic state
        - keep snapshot assembly outside the provider

    Not Responsible:
        - plugin registration
        - capability resolution
        - lifecycle management
        - plugin execution
    """
    knowledge_plugin = None

    if provider._builtin_registered:
        knowledge_plugin = provider.resolve_plugin(
            "knowledge",
            "knowledge",
        )

    return {
        "name": type(provider).__name__,
        "version": provider.VERSION,
        "manager": provider.manager.dump(),
        "factory": provider.factory.dump(),
        "capability_registry": (
            provider.capability_registry.dump()
        ),
        "knowledge_plugin": (
            knowledge_plugin.dump()
            if knowledge_plugin is not None
            else None
        ),
        "builtin_registered": (
            provider._builtin_registered
        ),
        "ready": provider.ready(),
    }


__all__ = [
    "build_plugin_provider_snapshot",
]
