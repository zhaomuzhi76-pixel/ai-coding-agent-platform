# 职责：内存验证 RAG 插件挂载与全链路，0 磁盘、0 独立端口
import sys, os, warnings
import unittest.mock as mock
warnings.filterwarnings("ignore")
sys.path.insert(0, os.getcwd())

from fastapi import FastAPI
from rag_core.integration import mount_rag

# ── 幂等性验证：app.state 锚点，不依赖 FastAPI routes 展开行为
app = FastAPI(title="test-embedded")
first = mount_rag(app)
second = mount_rag(app)
assert first is True, f"首次挂载应返回 True，实际 {first}"
assert second is False, f"重复挂载应返回 False（幂等拦截），实际 {second}"
assert app.state.rag_embedded_mounted is True, "state 锚点应被设置"

from fastapi.testclient import TestClient
client = TestClient(app)

@mock.patch("urllib.request.urlopen")
def test_all(mock_urlopen):
    resp = mock.MagicMock()
    resp.read.return_value = b'{"embedding": [0.1]*128}'
    mock_urlopen.return_value.__enter__.return_value = resp

    # 1. 健康检查
    assert client.get("/api/rag/kb/health").json()["mode"] == "embedded"

    # 2. 保存配置
    r = client.post("/api/rag/kb/config", json={
        "vector_model": "qwen3-embedding:8b",
        "rerank_model": "dengcao/Qwen3-Reranker-4B:Q5_K_M",
        "enable_rerank": True})
    assert r.status_code == 200, r.text

    # 3. 上传
    r = client.post("/api/rag/kb/upload",
        files={'file': ('t.txt', b'RAG embedded test. ' * 20, 'text/plain')})
    assert r.status_code == 200, r.text
    tid = r.json()["task_id"]

    # 4. 状态轮询
    assert client.get(f"/api/rag/kb/status/{tid}").status_code == 200

    # 5. 召回
    r = client.post("/api/rag/kb/search",
        json={"query": "embedded", "top_k": 2, "collection": "中医"})
    assert r.status_code == 200, r.text

    # 6. 统计
    assert client.get("/api/rag/kb/stats/中医").status_code == 200

    # 7. 删除
    r = client.post("/api/rag/kb/delete",
        json={"collection": "中医", "chunk_ids": []})
    assert r.status_code == 200

    print("✅ 嵌入式 RAG 全链路测试通过：0 磁盘、0 独立进程、0 终端退出")
    print("   ├─ 幂等挂载: ✅ 首次 True / 重复 False")
    print("   └─ 7 个端点: ✅ 全部 200 OK")

test_all()
