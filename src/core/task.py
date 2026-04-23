from dataclasses import dataclass
from enum import Enum, auto

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    DONE = auto()

@dataclass
class Task:
    id: str
    shelf_x: float
    shelf_y: float
    base_x: float
    base_y: float
    status: TaskStatus = TaskStatus.PENDING
class Task:
    def __init__(self, task_type, params):
        self.task_type = task_type  # e.g., 'move_to_shelf'
        self.params = params  # dict with parameters like {'x': 1.0, 'y': 2.0, 'aisle': 0}
