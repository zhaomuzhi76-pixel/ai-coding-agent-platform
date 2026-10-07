from __future__ import annotations

from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)
from backend.core.execution.llm_execution_contract import (
    LLMExecutionProviderProtocol,
)
from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.plugins.executors.assembly import (
    RuntimeExecutorAssembly,
)


class RuntimeExecutorPlugin:
    """
    Runtime executor plugin lifecycle boundary.

    Owns executor assembly, configuration and activation.
    """

    VERSION = "1.3"
    name = "executors"
    version = VERSION

    RESOLVER_CAPABILITY = RuntimeCapability(
        category="executor",
        name="resolver",
        version="1.0",
    )

    def __init__(self) -> None:
        self._assembly: (
            RuntimeExecutorAssembly | None
        ) = None
        self._capability_registry = None
        self._activated = False

    def configure(
        self,
        *,
        llm_provider: LLMExecutionProviderProtocol,
        tools,
        modification: CodeModificationProviderProtocol,
    ) -> None:
        self._validate_dependencies(
            llm_provider=llm_provider,
            tools=tools,
            modification=modification,
        )

        assembly = RuntimeExecutorAssembly(
            llm_provider=llm_provider,
            tools=tools,
            modification=modification,
        )

        if not self._assembly_dependencies_ready(
            assembly
        ):
            raise RuntimeError(
                "runtime executor assembly unavailable"
            )

        self._assembly = assembly
        self._activated = False
        self._capability_registry = None

    def activate(
        self,
        registry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        if not self._configured():
            raise RuntimeError(
                "executor plugin not configured"
            )

        if self._activated:
            return

        resolver = self._assembly.assemble()

        if not resolver.ready():
            raise RuntimeError(
                "executor resolver not ready"
            )

        registry.register(
            self.RESOLVER_CAPABILITY,
            resolver,
        )

        self._capability_registry = registry
        self._activated = True

    def create(self) -> object:
        if not self._configured():
            raise RuntimeError(
                "executor plugin not configured"
            )

        return self._assembly.assemble()

    def capabilities(self) -> list[RuntimeCapability]:
        return [self.RESOLVER_CAPABILITY]

    def register(
        self,
        registry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        self._capability_registry = registry

        if self._configured():
            self.activate(
                registry
            )

    def ready(self) -> bool:
        return (
            self._configured()
            and self._assembly.ready()
            and self._activated
            and self._capability_registry is not None
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": tuple(
                capability.key()
                for capability in self.capabilities()
            ),
            "configured": self._configured(),
            "activated": self._activated,
            "assembly": (
                self._assembly.dump()
                if self._assembly is not None
                else None
            ),
            "ready": self.ready(),
        }

    def _configured(self) -> bool:
        return self._assembly is not None

    @staticmethod
    def _assembly_dependencies_ready(
        assembly: RuntimeExecutorAssembly,
    ) -> bool:
        return all(
            value is not None
            for value in (
                assembly.llm_provider,
                assembly.tools,
                assembly.modification,
            )
        )

    @staticmethod
    def _validate_dependencies(
        *,
        llm_provider: LLMExecutionProviderProtocol,
        tools,
        modification: CodeModificationProviderProtocol,
    ) -> None:
        if llm_provider is None:
            raise ValueError(
                "llm provider required"
            )

        if tools is None:
            raise ValueError(
                "tool runtime required"
            )

        if modification is None:
            raise ValueError(
                "modification provider required"
            )

        if not isinstance(
            llm_provider,
            LLMExecutionProviderProtocol,
        ):
            raise TypeError(
                "llm provider runtime contract required"
            )

        if not isinstance(
            modification,
            CodeModificationProviderProtocol,
        ):
            raise TypeError(
                "modification runtime contract required"
            )


__all__ = [
    "RuntimeExecutorPlugin",
]
