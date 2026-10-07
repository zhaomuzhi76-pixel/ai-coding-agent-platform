# 职责：单例状态桥接层（配置、任务、存储、流水线），供嵌入式调用
from typing import Dict, Any
from ..config_manager import ConfigManager
from ..scheduler.task_manager import TaskManager
from ..parsers.txt_parser import TxtParser
from ..chunkers.simple_chunker import SimpleChunker
from ..embedders.ollama_embedder import OllamaEmbedder
from ..storage.partitioned_store import PartitionedVectorStore
from ..pipelines.ingestion_pipeline import IngestionPipeline
from ..pipelines.search_pipeline import SearchPipeline
from ..rerankers.ollama_reranker import OllamaReranker

class RAGBridge:
    """进程内单例，保证多个路由共享同一份内存状态。"""
    def __init__(self):
        self.config = ConfigManager()
        self.task_mgr = TaskManager()
        self.store = PartitionedVectorStore()
        self._rebuild()

    def _rebuild(self):
        cfg = self.config.get_config()
        self._pipeline = IngestionPipeline(
            TxtParser(), SimpleChunker(),
            OllamaEmbedder(cfg["vector_model"]),
            self.store, self.task_mgr
        )

    def get_ingestion(self) -> IngestionPipeline:
        return self._pipeline

    def get_search(self) -> SearchPipeline:
        cfg = self.config.get_config()
        return SearchPipeline(
            OllamaEmbedder(cfg["vector_model"]),
            self.store,
            OllamaReranker(cfg["rerank_model"])
        )

    def update_config(self, new_cfg: Dict[str, Any]) -> Dict[str, Any]:
        updated = self.config.update_config(new_cfg)
        self._rebuild()
        return updated

_bridge: RAGBridge = None
def get_bridge() -> RAGBridge:
    global _bridge
    if _bridge is None:
        _bridge = RAGBridge()
    return _bridge
