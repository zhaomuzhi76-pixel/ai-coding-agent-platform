from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.server.application_lifespan import (
    ApplicationLifespan,
)
from backend.api.ws_agent import router as ws_router
from backend.bootstrap import bootstrap, shutdown
from backend.assembly.fastapi_application import (
    create_application,
)

WS_ROUTE = "/ws/agent"
import time as _time
PROJECT_ID = f"ws-real-transport-gate-{int(_time.time())}"


def run() -> int:
    status = 0
    project_session_id: str | None = None
    project_registered = False

    print("===== WS REAL ASGI TRANSPORT GATE =====")

    lifespan = ApplicationLifespan(
        bootstrap=bootstrap,
        shutdown=shutdown,
    )

    app = create_application(
        lifespan=lifespan.lifespan,
        routers=(ws_router,),
    )

    with TestClient(app) as client:
        startup = lifespan.startup

        try:
            if startup is None or not startup.ready():
                raise RuntimeError(
                    "application startup unavailable"
                )

            import tempfile as _tf
            registration = startup.project_registration
            _tmp_root = _tf.mkdtemp(prefix="ws-gate-")
            registration.register(
                name=PROJECT_ID,
                root_path=_tmp_root,
                project_id=PROJECT_ID,
            )
            project_registered = True

            service = (
                startup.project_session_binding
                .operational
                .service
            )

            project_session = service.create_session(
                project_id=PROJECT_ID,
            )
            project_session_id = (
                project_session.session_id
            )

            service.start_session(
                project_session_id
            )

            active = service.get_session(
                project_session_id
            )

            if active.status != "active":
                raise RuntimeError(
                    "project session is not active"
                )

            print(
                "PROJECT_SESSION_ID=",
                project_session_id,
            )
            print(
                "PROJECT_SESSION_STATUS=",
                active.status,
            )
            print("PROJECT_SESSION_ACTIVE=PASS")

            with client.websocket_connect(
                WS_ROUTE
            ) as websocket:
                print("WS_CONNECTED=True")

                websocket.send_json(
                    {
                        "session_id": project_session_id,
                        "type": "message",
                        "message": "ping",
                        "workspace": _tmp_root,
                        "model": "qwen2.5-coder:7b",
                    }
                )

                print("WS_MESSAGE_SENT=True")

                response = websocket.receive_json()

                if not isinstance(response, dict):
                    raise RuntimeError(
                        "websocket response must be dict"
                    )

                response_session_id = response.get(
                    "session_id"
                )

                if not isinstance(
                    response_session_id,
                    str,
                ) or not response_session_id.strip():
                    raise RuntimeError(
                        "transport session id missing"
                    )

                if response_session_id == project_session_id:
                    raise RuntimeError(
                        "transport/project session "
                        "identity collapsed"
                    )

                print("WS_RESPONSE=", response)
                print(
                    "TRANSPORT_SESSION_ID=",
                    response_session_id,
                )
                print(
                    "PROJECT_SESSION_ID=",
                    project_session_id,
                )
                print("SESSION_IDENTITIES_SPLIT=PASS")
                print(
                    "PROJECT_SESSION_REACHED_RUNTIME_GATE=PASS"
                )
                print("WS_SESSION_ALIGNMENT=PASS")

        except Exception as exc:
            status = 1
            print(
                "WS_REAL_E2E_ERROR=",
                type(exc).__name__,
                str(exc),
            )

        finally:
            if startup is not None:
                service = (
                    startup.project_session_binding
                    .operational
                    .service
                )

                if project_session_id is not None:
                    try:
                        current = service.get_session(
                            project_session_id
                        )

                        if current.status == "active":
                            service.close_session(
                                project_session_id
                            )
                            print(
                                "PROJECT_SESSION_CLOSE=PASS"
                            )

                        removed = service.remove_session(
                            project_session_id
                        )

                        if not removed:
                            raise RuntimeError(
                                "project session cleanup "
                                "returned false"
                            )

                        print(
                            "PROJECT_SESSION_CLEANUP=PASS"
                        )

                    except Exception as exc:
                        status = 1
                        print(
                            "PROJECT_SESSION_CLEANUP_ERROR=",
                            type(exc).__name__,
                            str(exc),
                        )

                # 清理临时目录（幂等）
                try:
                    import shutil as _sh
                    _sh.rmtree(_tmp_root, ignore_errors=True)
                except Exception:  # silent-ok
                    pass

                if project_registered:
                    try:
                        startup.project_registration.remove(
                            PROJECT_ID
                        )
                        print("PROJECT_CLEANUP=PASS")
                    except Exception as exc:
                        status = 1
                        print(
                            "PROJECT_CLEANUP_ERROR=",
                            type(exc).__name__,
                            str(exc),
                        )

    print("WS_REAL_E2E_STATUS=", status)
    return status


if __name__ == "__main__":
    raise SystemExit(run())
