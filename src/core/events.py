from dataclasses import dataclass
from core.task import Task

@dataclass
class TaskReceivedEvent:
    task: Task

@dataclass
class AisleResponseEvent:
    aisle_id: str
    granted: bool