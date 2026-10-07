from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from backend.api.server.application_lifespan import ApplicationLifespan
from backend.api.ws_agent import router as ws_router
from backend.assembly.fastapi_application import create_application


HTTP_ROUTES = (
    ("/api/submission", 400),
)

REQUIRED_CONTEXT_KEYS = (
    "runtime_execution_gateway",
    "runtime_execution_session_flow_resolver",
    "agent_service",
    "runtime_submission",
    "project_session_service",
)


def _application():
    from backend.assembly.application_bootstrap_composition_factory import (
        ApplicationBootstrapCompositionFactory,
    )

    module = ApplicationBootstrapCompositionFactory().create(
        workspace_root=str(pathlib.Path.cwd()),
    )
    startup = module.startup

    def bootstrap():
        startup.start()
        return startup

    def shutdown():
        startup.stop()

    lifespan = ApplicationLifespan(
        bootstrap=bootstrap,
        shutdown=shutdown,
    )

    return create_application(
        lifespan=lifespan.lifespan,
        routers=(ws_router,),
    )


def check_transport() -> int:
    status = 0

    with TestClient(_application()) as client:
        for path, expected in HTTP_ROUTES:
            response = client.post(path, json={})
            passed = response.status_code == expected
            print(
                "HTTP", path,
                "STATUS=", response.status_code,
                "EXPECTED=", expected,
                "PASS=", passed,
            )
            status |= int(not passed)

        try:
            with client.websocket_connect(WS_ROUTE):
                print("WS", WS_ROUTE, "HANDSHAKE=PASS")
        except Exception as error:
            print(
                "WS", WS_ROUTE, "HANDSHAKE=FAIL",
                type(error).__name__, str(error),
            )
            status = 1

        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        for path, _ in HTTP_ROUTES:
            present = path in paths
            print("OPENAPI", path, "PRESENT=", present)
            status |= int(not present)

    return status


def check_startup() -> int:
    from backend.bootstrap import bootstrap, shutdown

    status = 0
    startup = bootstrap()

    try:
        ready = startup.ready()
        print("STARTUP_READY=", ready)
        status |= int(not ready)

        context = startup.state.context

        for key in REQUIRED_CONTEXT_KEYS:
            present = context.get(key) is not None
            print(f"CTX[{key}]=", present)
            status |= int(not present)

        resolver = context.get(
            "runtime_execution_session_flow_resolver"
        )
        resolver_bound = bool(
            resolver is not None
            and resolver.bound()
        )
        print(
            "RUNTIME_SESSION_FLOW_RESOLVER_BOUND=",
            resolver_bound,
        )
        status |= int(not resolver_bound)

        gateway = context.get("runtime_execution_gateway")
        execution_ready = bool(
            gateway is not None
            and gateway.ready()
            and gateway.execution_ready()
        )
        print(
            "GATEWAY_EXECUTION_READY=",
            execution_ready,
        )
        status |= int(not execution_ready)
    finally:
        shutdown()

    return status


def check_bypass() -> int:
    status = 0
    root = pathlib.Path("backend/application")
    allowed_owner = (
        root / "startup_application_execution_assembly.py"
    ).resolve()

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        text = path.read_text()

        if "self.agent.run(" in text:
            print("DIRECT_AGENT_BYPASS=", path)
            status = 1

        if "ApplicationContextFactory()" in text:
            allowed = path.resolve() == allowed_owner
            print(
                "CONTEXT_FACTORY_CONSTRUCTION=",
                path,
                "ALLOWED=",
                allowed,
            )
            status |= int(not allowed)

    return status


def check_compile() -> int:
    import compileall

    status = int(
        not compileall.compile_dir(
            "backend",
            quiet=1,
        )
    )
    print("COMPILE_STATUS=", status)
    return status


def check_size() -> int:
    status = 0

    for path in pathlib.Path("backend/api").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        lines = len(path.read_text().splitlines())
        if lines > 230:
            print("SIZE_FAIL=", lines, str(path))
            status = 1

    print("SIZE_STATUS=", status)
    return status


WS_ROUTE = "/ws/agent"


__all__ = [
    "check_transport",
    "check_startup",
    "check_bypass",
    "check_compile",
    "check_size",
]
