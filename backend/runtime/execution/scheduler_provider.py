from __future__ import annotations

from backend.runtime.contracts.node_events import (
    RuntimeNodeEventProducerProtocol,
)
from backend.runtime.execution.execution_contracts import (
    ExecutorResolverProtocol,
)
from backend.runtime.execution.node_batch_processor import (
    NodeBatchProcessor,
)
from backend.runtime.execution.node_event_producing_runner import (
    NodeEventProducingRunner,
)
from backend.runtime.execution.node_execution_runner import (
    NodeExecutionRunner,
)
from backend.runtime.execution.node_execution_service import (
    NodeExecutionService,
)
from backend.runtime.execution.runtime_node_input_materializer import (
    RuntimeNodeInputMaterializer,
)
from backend.runtime.execution.runtime_executable_query import (
    RuntimeExecutableQuery,
)
from backend.runtime.execution.runtime_dependency_failure_propagator import (
    RuntimeDependencyFailurePropagator,
)
from backend.runtime.execution.runtime_state_updater import (
    RuntimeStateUpdater,
)
from backend.runtime.execution.scheduler_batch_executor import (
    SchedulerBatchExecutor,
)
from backend.runtime.execution.scheduler_dispatch_guard import (
    SchedulerDispatchGuard,
)
from backend.runtime.execution.scheduler_dispatch_runner import (
    SchedulerDispatchRunner,
)
from backend.runtime.execution.scheduler_dispatcher import (
    SchedulerDispatcher,
)
from backend.runtime.execution.scheduler_node_selector import (
    SchedulerNodeSelector,
)
from backend.runtime.execution.scheduler_result_collector import (
    SchedulerResultCollector,
)
from backend.runtime.execution.scheduler_round_executor import (
    SchedulerRoundExecutor,
)


class SchedulerProvider:
    """
    Runtime scheduler composition boundary.
    """

    VERSION = "6.1"

    def __init__(
        self,
        *,
        executor_resolver: ExecutorResolverProtocol,
        state_updater: RuntimeStateUpdater,
        node_event_producer: RuntimeNodeEventProducerProtocol,
    ) -> None:
        if not isinstance(
            executor_resolver,
            ExecutorResolverProtocol,
        ):
            raise TypeError(
                "executor resolver contract required"
            )

        if state_updater is None:
            raise ValueError(
                "runtime state updater required"
            )

        if node_event_producer is None:
            raise ValueError(
                "node event producer required"
            )

        self.executor_resolver = executor_resolver
        self.state_updater = state_updater
        self.node_event_producer = node_event_producer

    def create_node_service(
        self,
    ) -> NodeExecutionService:
        return NodeExecutionService(
            self.executor_resolver
        )

    def create_node_runner(
        self,
    ) -> NodeEventProducingRunner:
        return NodeEventProducingRunner(
            runner=NodeExecutionRunner(
                self.create_node_service(),
                input_materializer=RuntimeNodeInputMaterializer(),
            ),
            producer=self.node_event_producer,
        )

    def create_node_processor(
        self,
    ) -> NodeBatchProcessor:
        return NodeBatchProcessor(
            runner=self.create_node_runner()
        )

    def create_selector(
        self,
    ) -> SchedulerNodeSelector:
        return SchedulerNodeSelector(
            RuntimeExecutableQuery()
        )

    def create_batch_executor(
        self,
    ) -> SchedulerBatchExecutor:
        return SchedulerBatchExecutor(
            processor=self.create_node_processor(),
            collector=SchedulerResultCollector(),
        )

    def create_round_executor(
        self,
    ) -> SchedulerRoundExecutor:
        return SchedulerRoundExecutor(
            executor=self.create_batch_executor(),
            selector=self.create_selector(),
            state_updater=self.state_updater,
            failure_propagator=(
                RuntimeDependencyFailurePropagator()
            ),
        )

    def create_runner(
        self,
    ) -> SchedulerDispatchRunner:
        return SchedulerDispatchRunner(
            self.create_round_executor()
        )

    def create(
        self,
    ) -> SchedulerDispatcher:
        return SchedulerDispatcher(
            runner=self.create_runner(),
            guard=SchedulerDispatchGuard(),
        )

    def ready(
        self,
    ) -> bool:
        return all(
            (
                self.executor_resolver.ready(),
                self.state_updater.ready(),
                self.node_event_producer.ready(),
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


__all__ = [
    "SchedulerProvider",
]
