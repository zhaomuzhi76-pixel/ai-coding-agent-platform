from backend.core.plugins.assembly import (
    PluginAssembly,
)

from backend.core.plugins.discovery import (
    PluginDiscovery,
)

from backend.core.plugins.plugin_component import (
    PluginComponentProtocol,
)

from backend.core.plugins.plugin_target import (
    PluginTargetProtocol,
)

from backend.core.plugins.contract import (
    PluginContributor,
)

from backend.core.plugins.contributor_registry import (
    ContributorRegistry,
)


__all__ = [
    "PluginAssembly",
    "PluginDiscovery",
    "PluginComponentProtocol",
    "PluginTargetProtocol",
    "PluginContributor",
    "ContributorRegistry",
]
