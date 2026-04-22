from dataclasses import dataclass
from typing import Callable, List

@dataclass
class ScheduledTask:
    interval_s: float
    callback: Callable
    last_run: float = 0.0

class Scheduler:
    def __init__(self):
        self.tasks: List[ScheduledTask] = []

    def add(self, task: ScheduledTask):
        self.tasks.append(task)

    def update(self, current_time: float):
        for task in self.tasks:
            if current_time - task.last_run >= task.interval_s:
                task.callback()
                task.last_run = current_time