from ..models import TaskState
from ..interfaces import IParser, IChunker, IEmbedder, IVectorStore
from ..scheduler.task_manager import TaskManager

class IngestionPipeline:
    def __init__(self, parser: IParser, chunker: IChunker, embedder: IEmbedder, store: IVectorStore, tm: TaskManager):
        self.parser = parser
        self.chunker = chunker
        self.embedder = embedder
        self.store = store
        self.tm = tm

    def run(self, task_id: str, content: bytes, filename: str):
        try:
            # 1. 解析阶段
            self.tm.update_state(task_id, TaskState.PARSING, 10.0)
            if self.tm.is_cancelled(task_id): return self._cancel(task_id)
            doc = self.parser.parse(content, filename)

            # 2. 生成草稿阶段 (UI中显示的节点)
            self.tm.update_state(task_id, TaskState.CHUNKING, 30.0)
            if self.tm.is_cancelled(task_id): return self._cancel(task_id)
            chunks = self.chunker.chunk(doc)

            # 3. 生成向量阶段 (UI中显示的节点)
            self.tm.update_state(task_id, TaskState.EMBEDDING, 60.0)
            if self.tm.is_cancelled(task_id): return self._cancel(task_id)
            texts = [c.text for c in chunks]
            vectors = self.embedder.embed(texts)

            # 4. 入库
            self.tm.update_state(task_id, TaskState.EMBEDDING, 90.0)
            self.store.insert(chunks, vectors)

            self.tm.finish_task(task_id, TaskState.SUCCESS)
        except Exception as e:
            self.tm.finish_task(task_id, TaskState.FAILED, str(e))

    def _cancel(self, task_id: str):
        self.tm.finish_task(task_id, TaskState.CANCELLED)
