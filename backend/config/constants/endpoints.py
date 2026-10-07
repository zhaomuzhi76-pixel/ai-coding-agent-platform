"""本地服务端点常量（工业级模块化）。

职责：
    - 集中管理所有**本地**服务地址（host / port / url）
    - 环境变量可覆盖（BACKEND_PORT / OLLAMA_PORT / ...）

不负责：
    - 云 API 端点（Anthropic / OpenAI / DashScope / 智谱）→ 属业务常量
    - 业务数字阈值（max_chars / max_rows / timeout）→ 属各模块
"""
from __future__ import annotations

import os
from typing import Final

# ── 主机 ──
LOCALHOST: Final[str] = "127.0.0.1"
ALL_INTERFACES: Final[str] = "0.0.0.0"

# ── 端口（可用环境变量覆盖） ──
BACKEND_PORT: Final[int]  = int(os.getenv("BACKEND_PORT",  "9022"))
OLLAMA_PORT: Final[int]   = int(os.getenv("OLLAMA_PORT",   "11434"))
RERANKER_PORT: Final[int] = int(os.getenv("RERANKER_PORT", "9033"))
QDRANT_PORT: Final[int]   = int(os.getenv("QDRANT_PORT",   "6333"))
MONGODB_PORT: Final[int]  = int(os.getenv("MONGODB_PORT",  "27017"))
REDIS_PORT: Final[int]    = int(os.getenv("REDIS_PORT",    "6379"))
SD_PORT: Final[int]       = int(os.getenv("SD_PORT",       "7860"))

# ── URL（由 host + port 派生） ──
OLLAMA_URL:   Final[str] = f"http://{LOCALHOST}:{OLLAMA_PORT}"
RERANKER_URL: Final[str] = f"http://{LOCALHOST}:{RERANKER_PORT}"
QDRANT_URL:   Final[str] = f"http://{LOCALHOST}:{QDRANT_PORT}"
MONGODB_URL:  Final[str] = f"mongodb://localhost:{MONGODB_PORT}"
REDIS_URL:    Final[str] = f"redis://localhost:{REDIS_PORT}/0"
SD_URL:       Final[str] = f"http://{LOCALHOST}:{SD_PORT}"

__all__ = [
    "ALL_INTERFACES", "BACKEND_PORT", "LOCALHOST",
    "MONGODB_PORT", "MONGODB_URL", "OLLAMA_PORT", "OLLAMA_URL",
    "QDRANT_PORT", "QDRANT_URL", "REDIS_PORT", "REDIS_URL",
    "RERANKER_PORT", "RERANKER_URL", "SD_PORT", "SD_URL",
]
