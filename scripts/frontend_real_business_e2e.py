import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
import websocket
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
BACKEND = "http://127.0.0.1:9022"
VITE = "http://127.0.0.1:4173"
PROJECT_ID = "frontend-e2e-project"
SESSION_ID = "frontend-e2e-session"
processes = []
def request(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        text = response.read().decode()
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            value = text
        return response.status, value
def wait_url(url, timeout=30, process=None):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            output, _ = process.communicate(timeout=1)
            raise RuntimeError(
                f"process exited before {url}: "
                f"code={process.returncode}\n{output}"
            )
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return response.status, response.read()
        except Exception as error:
            last = error
            time.sleep(0.25)
    if process is not None and process.poll() is not None:
        output, _ = process.communicate(timeout=1)
        raise RuntimeError(
            f"process exited before {url}: "
            f"code={process.returncode}\n{output}"
        )
    raise RuntimeError(f"timeout: {url}: {last}")
def start(command, cwd):
    env = dict(__import__("os").environ)
    env["PYTHONUNBUFFERED"] = "1"
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    processes.append(process)
    return process
def cleanup():
    for process in reversed(processes):
        process.terminate()
    for process in reversed(processes):
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
def check_http_business_flow():
    status, health = request("GET", f"{VITE}/api/health")
    assert status == 200 and health == {"status": "ok"}
    print("REAL_FRONTEND_API_PROXY=PASS")
    status, project = request("POST", f"{VITE}/api/projects", {
        "project_id": PROJECT_ID,
        "name": PROJECT_ID,
        "root_path": str(ROOT),
    })
    assert status == 200
    assert project["project"]["project_id"] == PROJECT_ID
    print("REAL_PROJECT_CREATE=PASS")
    status, session = request("POST", f"{VITE}/api/project-sessions", {
        "project_id": PROJECT_ID,
        "session_id": SESSION_ID,
    })
    assert status == 200 and session["session_id"] == SESSION_ID
    print("REAL_SESSION_CREATE=PASS")
    status, session = request(
        "POST",
        f"{VITE}/api/project-sessions/{SESSION_ID}/start",
    )
    assert status == 200 and session["status"] == "active"
    print("REAL_SESSION_START=PASS")
    status, active = request(
        "GET",
        f"{VITE}/api/project-sessions/active",
    )
    assert status == 200
    assert any(
        item["session_id"] == SESSION_ID
        for item in active["sessions"]
    )
    print("REAL_ACTIVE_SESSION=PASS")
def check_ws_and_submission():
    socket = websocket.create_connection(
        "ws://127.0.0.1:4173/ws/agent",
        timeout=15,
    )
    try:
        print("REAL_WS_HANDSHAKE=PASS")
        socket.send(json.dumps({
            "session_id": SESSION_ID,
            "message": "health check",
            "model": "qwen2.5-coder:7b",
        }))
        socket.settimeout(5)
        assert socket.recv()
        print("REAL_WS_EVENT=PASS")
    finally:
        socket.close()
        print("REAL_WS_DISCONNECT=PASS")
    status, result = request(
        "POST",
        f"{VITE}/api/submission",
        {
            "session_id": SESSION_ID,
            "message": "Return a concise health confirmation.",
            "model": "qwen2.5-coder:7b",
        },
    )
    assert status == 200 and isinstance(result, dict)
    print("REAL_SUBMISSION=PASS")
def check_session_lifecycle():
    status, fetched = request(
        "GET",
        f"{VITE}/api/project-sessions/{SESSION_ID}",
    )
    assert status == 200 and fetched["session_id"] == SESSION_ID
    print("REAL_SESSION_FIDELITY=PASS")
    status, closed = request(
        "POST",
        f"{VITE}/api/project-sessions/{SESSION_ID}/close",
    )
    assert status == 200
    print("REAL_SESSION_CLOSE=PASS")
    try:
        request(
            "POST",
            f"{VITE}/api/project-sessions/{SESSION_ID}/start",
        )
    except urllib.error.HTTPError as error:
        assert error.code in (400, 404, 409, 422, 500, 503)
        print("REAL_CLOSED_SESSION_REJECT=PASS")
    else:
        raise AssertionError(
            "closed session unexpectedly restarted"
        )
    status, removed = request(
        "DELETE",
        f"{VITE}/api/project-sessions/{SESSION_ID}",
    )
    assert status == 200 and removed["removed"] is True
    print("REAL_SESSION_REMOVE=PASS")
    status, project_removed = request(
        "DELETE",
        f"{VITE}/api/projects/{PROJECT_ID}",
    )
    assert status == 200
    print("REAL_PROJECT_REMOVE=PASS")
def main():
    print("=" * 120)
    print("FRONTEND_REAL_BUSINESS_E2E_GATE")
    print("=" * 120)
    try:
        backend_process = start(["python", "-m", "backend"], ROOT)
        status, body = wait_url(
            f"{BACKEND}/health",
            process=backend_process,
        )
        assert status == 200
        assert json.loads(body.decode())["status"] == "ok"
        print("REAL_BACKEND_HEALTH=PASS")
        frontend_process = start(
            [
                "npm",
                "run",
                "dev",
                "--",
                "--host",
                "127.0.0.1",
                "--port",
                "4173",
            ],
            FRONTEND,
        )
        status, body = wait_url(
            f"{VITE}/index.html",
            process=frontend_process,
        )
        assert status == 200 and b"<html" in body.lower()
        print("REAL_FRONTEND_START=PASS")
        check_http_business_flow()
        check_ws_and_submission()
        check_session_lifecycle()
    finally:
        cleanup()
    print("REAL_PROCESS_CLEANUP=PASS")
    print("FRONTEND_REAL_BUSINESS_E2E_GATE=PASS")
    print("=" * 120)
if __name__ == "__main__":
    main()
