import uuid
import time
from typing import Dict, Any, Callable
from ..models import TaskInfo, TaskState

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}

    def create_task(self, filename: str) -> str:
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = TaskInfo(task_id=task_id, filename=filename)
        return task_id

    def update_state(self, task_id: str, state: TaskState, progress: float):
        if task_id in self.tasks:
            self.tasks[task_id].state = state
            self.tasks[task_id].progress = progress

    def cancel_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].cancel_requested = True

    def is_cancelled(self, task_id: str) -> bool:
        return self.tasks.get(task_id, TaskInfo("", "")).cancel_requested

    def finish_task(self, task_id: str, state: TaskState, error_msg: str = ""):
        if task_id in self.tasks:
            self.tasks[task_id].state = state
            self.tasks[task_id].error_msg = error_msg
            self.tasks[task_id].end_time = time.time()
            self.tasks[task_id].progress = 100.0 if state == TaskState.SUCCESS else self.tasks[task_id].progress
