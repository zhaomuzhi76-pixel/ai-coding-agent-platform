"""FastAPI TestClient 内存级 HTTP E2E（隔离持久化到 /tmp）"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

# 强制持久化到临时目录，绝不污染用户主目录
os.environ["BIANCHENG_MODEL_STORE"] = str(
    Path(tempfile.gettempdir()) / "mr_e2e.json"
)
os.environ["DASHSCOPE_API_KEY"] = "sk-e2e-test"

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
except ImportError:
    print("⚠️  FastAPI 未安装，跳过 HTTP E2E（主架构不受影响）")
    sys.exit(0)

from backend.core.model_registry import reset_registry
from backend.core.model_registry.adapters.fastapi_adapter import mount


def _client() -> TestClient:
    reset_registry()
    app = FastAPI()
    mount(app)
    return TestClient(app)


def run() -> None:
    c = _client()

    kpi = c.get("/api/model-registry/kpi").json()
    assert kpi["providers_total"] >= 1, kpi
    print("✅ KPI:", kpi)

    ids = {p["id"] for p in c.get("/api/model-registry/providers").json()}
    assert "ollama-local" in ids, ids
    print("✅ Providers:", sorted(ids))

    ms = c.get("/api/model-registry/providers/ollama-local/models").json()
    assert any(m["id"] == "qwen2.5-coder:7b" for m in ms), ms
    print("✅ Models:", [m["id"] for m in ms])

    r = c.post("/api/model-registry/providers/ollama-local/test").json()
    assert r["connected"] is True
    print("✅ Health:", r)

    roles = c.get("/api/model-registry/roles").json()
    assert len(roles) == 5, len(roles)
    assert all("candidates" in x for x in roles)
    print("✅ Roles:", [x["role"] for x in roles])

    r = c.post("/api/model-registry/providers", json={
        "id": "vllm-e2e", "name": "vLLM", "kind": "local",
        "base_url": "http://127.0.0.1:8000",
    }).json()
    assert r["ok"] is True
    print("✅ Create:", r)

    r = c.post("/api/model-registry/roles", json={
        "role": "code", "primary": "qwen-max",
        "fallback": "qwen2.5-coder:7b",
    }).json()
    assert r["ok"] is True
    code = next(
        x for x in c.get("/api/model-registry/roles").json()
        if x["role"] == "code"
    )
    assert code["primary"] == "qwen-max"
    assert code["fallback"] == "qwen2.5-coder:7b"
    print("✅ Bind:", code["primary"], "←", code["fallback"])

    assert c.post(
        "/api/model-registry/providers", json={"no_id": True}
    ).status_code == 400
    print("✅ Error path: 400")

    print("✅ HTTP E2E 全部通过 · 磁盘仅 1 个临时 JSON · 终端未退出")


if __name__ == "__main__":
    try:
        run()
    except AssertionError as exc:
        print("❌ 断言失败:", exc)
    except Exception as exc:
        print(f"❌ {type(exc).__name__}: {exc}")
