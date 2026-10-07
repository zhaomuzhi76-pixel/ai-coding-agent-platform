import sys
import os
sys.path.insert(0, os.getcwd())
from rag_core.parsers.txt_parser import TxtParser
from rag_core.chunkers.simple_chunker import SimpleChunker
from rag_core.embedders.mock_embedder import MockEmbedder
from rag_core.storage.memory_store import MemoryVectorStore
from rag_core.scheduler.task_manager import TaskManager
from rag_core.pipelines.ingestion_pipeline import IngestionPipeline

def test_industrial_rag():
    tm = TaskManager()
    pipeline = IngestionPipeline(TxtParser(), SimpleChunker(), MockEmbedder(), MemoryVectorStore(), tm)
    task_id = tm.create_task("test_clean.txt")
    
    # 纯内存测试，不写入任何临时文件，0硬盘占用
    mock_content = b"RAG (Retrieval-Augmented Generation) is a technique that enhances LLMs with external knowledge. " * 10
    pipeline.run(task_id, mock_content, "test_clean.txt")
    
    task_info = tm.tasks[task_id]
    assert task_info.state.value == "SUCCESS", f"Task failed: {task_info.error_msg}"
    assert task_info.progress == 100.0
    print("✅ 工业级严格测试通过：0 磁盘占用，全链路闭环。")

if __name__ == "__main__":
    test_industrial_rag()
