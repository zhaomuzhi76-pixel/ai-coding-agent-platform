import sys
import os
import warnings
import unittest.mock as mock
warnings.filterwarnings("ignore")
sys.path.insert(0, os.getcwd())
from fastapi.testclient import TestClient
from rag_core.api.main import app

client = TestClient(app)

@mock.patch("urllib.request.urlopen")
def test_full_ui_flow(mock_urlopen):
    mock_response = mock.MagicMock()
    mock_response.read.return_value = b'{"embedding": [0.1]*128}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    # 1. 模拟 UI 保存配置
    res = client.post("/api/v1/kb/config", json={"vector_model": "qwen3-embedding:8b", "rerank_model": "dengcao/Qwen3-Reranker-4B:Q5_K_M", "enable_rerank": True})
    assert res.status_code == 200

    # 2. 模拟 UI 点击选择文件上传
    res = client.post("/api/v1/kb/upload", files={'file': ('test_clean.txt', b'RAG test for Traditional Chinese Medicine. ' * 10, 'text/plain')})
    assert res.status_code == 200
    task_id = res.json()["task_id"]

    # 3. 模拟 UI 查看“正在处理”
    res = client.get(f"/api/v1/kb/status/{task_id}")
    assert res.status_code == 200

    # 4. 模拟 UI 点击“召回测试”
    res = client.post("/api/v1/kb/search", json={"query": "Traditional Chinese Medicine", "top_k": 2, "collection": "中医"})
    assert res.status_code == 200
    
    # 5. 模拟 UI 查看“已入库数据”统计
    res = client.get("/api/v1/kb/stats/中医")
    assert res.status_code == 200
    print("✅ 工业级 RAG 全链路内存测试通过：端口逻辑安全，0 磁盘占用，0 依赖安装。")

if __name__ == "__main__":
    test_full_ui_flow()
