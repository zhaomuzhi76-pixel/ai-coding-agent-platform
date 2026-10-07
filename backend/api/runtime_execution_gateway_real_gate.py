from __future__ import annotations

import inspect


def run() -> int:
    import backend.bootstrap as bootstrap

    from backend.application.runtime_execution_gateway import (
        ApplicationRuntimeExecutionGateway,
        ApplicationRuntimeExecutionGatewayContract,
    )

    status = 0

    print(
        "============================================================"
    )
    print(
        " RUNTIME EXECUTION GATEWAY REAL WHOLE-LAYER GATE"
    )
    print(
        "============================================================"
    )

    try:
        startup = bootstrap.bootstrap()

        gateway = startup.execution_gateway

        print(
            "STARTUP_READY=",
            startup.ready(),
        )
        print(
            "GATEWAY_TYPE=",
            type(gateway).__name__
            if gateway is not None
            else None,
        )
        print(
            "GATEWAY_IS_CONTRACT=",
            isinstance(
                gateway,
                ApplicationRuntimeExecutionGatewayContract,
            ),
        )
        print(
            "GATEWAY_READY=",
            gateway.ready()
            if gateway is not None
            else False,
        )
        print(
            "GATEWAY_EXECUTION_READY=",
            gateway.execution_ready()
            if gateway is not None
            else False,
        )

        resolver = getattr(
            gateway,
            "flow_resolver",
            None,
        )

        flow = (
            resolver.resolve()
            if resolver is not None
            else None
        )

        print(
            "RESOLVER_TYPE=",
            type(resolver).__name__
            if resolver is not None
            else None,
        )
        print(
            "RESOLVER_BOUND=",
            resolver.bound()
            if resolver is not None
            else False,
        )
        print(
            "FLOW_TYPE=",
            type(flow).__name__
            if flow is not None
            else None,
        )
        print(
            "FLOW_READY=",
            flow.ready()
            if flow is not None
            else False,
        )

        signature = inspect.signature(
            ApplicationRuntimeExecutionGateway.execute
        )

        contract_execute = inspect.signature(
            ApplicationRuntimeExecutionGatewayContract.execute
        )

        implementation_public = {
            name
            for name, value in inspect.getmembers(
                ApplicationRuntimeExecutionGateway,
                predicate=inspect.isfunction,
            )
            if not name.startswith("_")
        }

        contract_public = {
            name
            for name, value in inspect.getmembers(
                ApplicationRuntimeExecutionGatewayContract,
                predicate=inspect.isfunction,
            )
            if not name.startswith("_")
        }

        print(
            "EXECUTE_SIGNATURE=",
            signature,
        )
        print(
            "CONTRACT_EXECUTE_SIGNATURE=",
            contract_execute,
        )
        print(
            "IMPLEMENTATION_PUBLIC=",
            sorted(implementation_public),
        )
        print(
            "CONTRACT_PUBLIC=",
            sorted(contract_public),
        )

        if not startup.ready():
            raise RuntimeError(
                "application startup not ready"
            )

        if not isinstance(
            gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise RuntimeError(
                "runtime gateway contract check failed"
            )

        if not gateway.ready():
            raise RuntimeError(
                "runtime gateway not ready"
            )

        if not gateway.execution_ready():
            raise RuntimeError(
                "runtime gateway not execution-ready"
            )

        if resolver is None or not resolver.bound():
            raise RuntimeError(
                "runtime session flow resolver not bound"
            )

        if flow is None or not flow.ready():
            raise RuntimeError(
                "runtime session flow not ready"
            )

        if implementation_public != contract_public:
            raise RuntimeError(
                "gateway contract public-method parity failure"
            )

        print("REAL_STARTUP_GATE=PASS")

    except Exception as error:
        status = 1
        import traceback
        traceback.print_exc()
        print(
            "REAL_STARTUP_GATE_ERROR=",
            type(error).__name__,
            str(error),
        )

    finally:
        bootstrap.shutdown()

    return status


if __name__ == "__main__":
    run()
