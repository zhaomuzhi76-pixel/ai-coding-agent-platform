from backend.assembly.contracts import (
    AssemblyModuleProtocol,
    AssemblyPipelineProtocol,
)
from backend.assembly.lifecycle import (
    AssemblyLifecycle,
    AssemblyLifecycleState,
)
from backend.assembly.module import (
    AssemblyModule,
)
from backend.assembly.pipeline import (
    AssemblyPipeline,
)
from backend.assembly.registry import (
    AssemblyRegistry,
)
from backend.assembly.runtime import (
    AssemblyRuntime,
)
from backend.assembly.startup_module import (
    ApplicationStartupModule,
)

__all__ = [
    "AssemblyModuleProtocol",
    "AssemblyPipelineProtocol",
    "AssemblyLifecycle",
    "AssemblyLifecycleState",
    "AssemblyModule",
    "AssemblyPipeline",
    "AssemblyRegistry",
    "AssemblyRuntime",
    "ApplicationStartupModule",
]
from backend.assembly.runtime_factory import (
    AssemblyRuntimeFactory,
)

__all__ = [
    *globals().get("__all__", ()),
    "AssemblyRuntimeFactory",
]
