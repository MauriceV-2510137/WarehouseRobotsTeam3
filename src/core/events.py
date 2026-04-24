from dataclasses import dataclass
from core.task import Task

class Event:
    pass

@dataclass
class TaskReceivedEvent(Event):
    task: Task

@dataclass
class AisleResponseEvent(Event):
    aisle_id: str
    granted: bool