# 职责：全局配置管理（对接UI中的“向量模型、重排序模型、保存配置”）
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config = {
            "vector_model": "qwen3-embedding:8b",
            "rerank_model": "dengcao/Qwen3-Reranker-4B:Q5_K_M",
            "enable_rerank": True,
            "domain": "中医",
            "collection_name": "agent_code_knowledge"
        }
    def get_config(self) -> Dict[str, Any]:
        return self.config
    def update_config(self, new_config: Dict[str, Any]):
        self.config.update(new_config)
        return self.config
