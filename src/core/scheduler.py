from dataclasses import dataclass, field
from typing import Callable

@dataclass
class ScheduledTask:
    interval_s: float
    callback: Callable[[], None]
    accumulator: float = field(default=0.0)

class Scheduler:
    def __init__(self) -> None:
        self.tasks: list[ScheduledTask] = []

    def add(self, task: ScheduledTask) -> None:
        self.tasks.append(task)

    def update(self, dt: float) -> None:
        for task in self.tasks:

            task.accumulator += dt

            while task.accumulator >= task.interval_s:
                task.callback()
                task.accumulator -= task.interval_s