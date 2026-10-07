from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import time

class TaskState(str, Enum):
    PENDING = "PENDING"
    PARSING = "PARSING"
    CHUNKING = "CHUNKING" # 生成草稿
    EMBEDDING = "EMBEDDING" # 生成向量
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class TaskInfo:
    task_id: str
    filename: str
    state: TaskState = TaskState.PENDING
    progress: float = 0.0
    error_msg: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    cancel_requested: bool = False

@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Document:
    doc_id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
