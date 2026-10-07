from __future__ import annotations

from backend.tests.gates.transport_real_e2e_gate_support import (
    check_bypass,
    check_compile,
    check_size,
    check_startup,
    check_transport,
)


def main_gate() -> int:
    print("\n===== 01 REAL TRANSPORT =====")
    route_status = check_transport()

    print("\n===== 02 STARTUP GRAPH =====")
    startup_status = check_startup()

    print("\n===== 03 BYPASS SEARCH =====")
    bypass_status = check_bypass()

    print("\n===== 04 COMPILE =====")
    compile_status = check_compile()

    print("\n===== 05 SIZE =====")
    size_status = check_size()

    final = (
        route_status
        or startup_status
        or bypass_status
        or compile_status
        or size_status
    )

    print("\n===== FINAL TRANSPORT GATE =====")
    print("ROUTE_STATUS=", route_status)
    print("STARTUP_STATUS=", startup_status)
    print("BYPASS_STATUS=", bypass_status)
    print("COMPILE_STATUS=", compile_status)
    print("SIZE_STATUS=", size_status)
    print(
        "TRANSPORT_REAL_ENTRY_LAYER=",
        "NOT_FROZEN" if final else "FROZEN",
    )

    return int(final)


if __name__ == "__main__":
    main_gate()
