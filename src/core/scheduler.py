from dataclasses import dataclass
from typing import Callable, List

@dataclass
class ScheduledTask:
    interval_s: float
    callback: Callable
    accumulator: float = 0.0

class Scheduler:
    def __init__(self):
        self.tasks: List[ScheduledTask] = []

    def add(self, task: ScheduledTask):
        self.tasks.append(task)

    def update(self, dt: float):
        for task in self.tasks:

            task.accumulator += dt

            if task.accumulator >= task.interval_s:
                task.callback()
                task.accumulator -= task.interval_s