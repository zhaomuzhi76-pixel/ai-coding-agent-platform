from __future__ import annotations


import importlib


from backend.runtime.plugin.plugin_manifest import (
    RuntimePluginManifest,
)



class RuntimePluginResolver:
    """
    Runtime plugin entry resolver.


    Responsibility:

        - resolve plugin entry from manifest
        - create plugin instance


    Not Responsible:

        - plugin loading lifecycle
        - capability execution
        - plugin management
    """


    VERSION = "1.0"



    def resolve(
        self,
        manifest: RuntimePluginManifest,
    ) -> object:

        if not manifest.ready():
            raise ValueError(
                "invalid plugin manifest"
            )


        module = importlib.import_module(
            manifest.module
        )


        entry = getattr(
            module,
            manifest.entry,
            None,
        )


        if entry is None:
            raise RuntimeError(
                "plugin entry unavailable:"
                f"{manifest.entry}"
            )


        return entry()



    def ready(
        self,
    ) -> bool:

        return True



    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "ready":
                self.ready(),
        }



__all__ = [
    "RuntimePluginResolver",
]
