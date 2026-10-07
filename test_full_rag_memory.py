import sys
import os
import warnings
import unittest.mock as mock
warnings.filterwarnings("ignore")  # 忽略 httpx 弃用警告
sys.path.insert(0, os.getcwd())
from fastapi.testclient import TestClient
from rag_core.api.main import app

client = TestClient(app)

@mock.patch("urllib.request.urlopen")
def test_full_ui_flow(mock_urlopen):
    # 拦截 Ollama 的网络请求，实现纯内存测试
    mock_response = mock.MagicMock()
    mock_response.read.return_value = b'{"embedding": [0.1]*128}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    # 1. 模拟 UI 保存配置
    config_payload = {"vector_model": "qwen3-embedding:8b", "rerank_model": "dengcao/Qwen3-Reranker-4B:Q5_K_M", "enable_rerank": True}
    res = client.post("/api/v1/kb/config", json=config_payload)
    assert res.status_code == 200, f"Config failed: {res.text}"

    # 2. 模拟 UI 点击选择文件上传
    files = {'file': ('test_clean.txt', b'RAG test for Traditional Chinese Medicine. ' * 10, 'text/plain')}
    res = client.post("/api/v1/kb/upload", files=files)
    assert res.status_code == 200, f"Upload failed: {res.text}"
    task_id = res.json()["task_id"]

    # 3. 模拟 UI 查看“正在处理”
    res = client.get(f"/api/v1/kb/status/{task_id}")
    assert res.status_code == 200, f"Status failed: {res.text}"

    # 4. 模拟 UI 点击“召回测试”
    res = client.post("/api/v1/kb/search", json={"query": "Traditional Chinese Medicine", "top_k": 2, "collection": "中医"})
    assert res.status_code == 200, f"Search failed: {res.text}"
    
    # 5. 模拟 UI 查看“已入库数据”统计
    res = client.get("/api/v1/kb/stats/中医")
    assert res.status_code == 200, f"Stats failed: {res.text}"
    print("✅ 工业级 RAG 知识库全链路 API 测试通过：0 磁盘占用，0 依赖安装。")

if __name__ == "__main__":
    test_full_ui_flow()
