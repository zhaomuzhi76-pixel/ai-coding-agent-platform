from __future__ import annotations

from backend.runtime.contracts.execution import (
    RuntimeExecutionProtocol,
)
from backend.runtime.execution.dag_execution_cycle_provider import (
    DAGExecutionCycleProvider,
)
from backend.runtime.execution.dag_execution_loop_provider import (
    DAGExecutionLoopProvider,
)
from backend.runtime.execution.dag_execution_round_provider import (
    DAGExecutionRoundProvider,
)
from backend.runtime.execution.runtime_execution_context_provider import (
    RuntimeExecutionContextProvider,
)
from backend.runtime.execution.runtime_state_updater import (
    RuntimeStateUpdater,
)
from backend.runtime.execution.scheduler_provider import (
    SchedulerProvider,
)
from backend.runtime.plugin.capability import (
    RuntimeCapability,
)


class DAGExecutionEngineProvider:
    """
    DAG execution engine composition root.
    """

    VERSION = "1.2"

    EXECUTOR_RESOLVER = RuntimeCapability(
        category="executor",
        name="resolver",
        version="1.0",
    )

    NODE_EVENT_PRODUCER = RuntimeCapability(
        category="events",
        name="node_producer",
        version="1.0",
    )

    def __init__(
        self,
        capability_registry,
        context_provider: RuntimeExecutionContextProvider | None = None,
    ) -> None:
        if capability_registry is None:
            raise ValueError(
                "capability registry required"
            )

        self.capability_registry = capability_registry
        self.context_provider = (
            context_provider
            if context_provider is not None
            else RuntimeExecutionContextProvider()
        )

        self.loop_provider = None

    def create(
        self,
    ) -> RuntimeExecutionProtocol:

        resolver = self.capability_registry.resolve(
            self.EXECUTOR_RESOLVER
        )

        producer = self.capability_registry.resolve(
            self.NODE_EVENT_PRODUCER
        )

        scheduler = SchedulerProvider(
            executor_resolver=resolver,
            state_updater=RuntimeStateUpdater(),
            node_event_producer=producer,
        )

        if not scheduler.ready():
            raise RuntimeError(
                "scheduler unavailable"
            )

        round_provider = DAGExecutionRoundProvider(
            dispatcher=scheduler.create(),
        )

        cycle_provider = DAGExecutionCycleProvider(
            round_provider=round_provider,
        )

        self.loop_provider = DAGExecutionLoopProvider(
            cycle_provider=cycle_provider,
        )

        context = self.context_provider.create()

        if not context.ready():
            raise RuntimeError(
                "execution context unavailable"
            )

        return self._create_engine(
            loop=self.loop_provider.create(),
            execution_context=context,
        )

    def ready(
        self,
    ) -> bool:
        return all(
            (
                self.context_provider.ready(),
                self.capability_registry.exists(
                    self.EXECUTOR_RESOLVER
                ),
                self.capability_registry.exists(
                    self.NODE_EVENT_PRODUCER
                ),
            )
        )

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }

    @staticmethod
    def _create_engine(
        *,
        loop,
        execution_context,
    ) -> RuntimeExecutionProtocol:
        from backend.runtime.execution.runtime_execution_executor import (
            RuntimeExecutionExecutor,
        )

        return RuntimeExecutionExecutor(
            loop=loop,
            execution_context=execution_context,
        )


__all__ = [
    "DAGExecutionEngineProvider",
]
