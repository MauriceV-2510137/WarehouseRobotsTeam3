from core.task import Task, TaskStatus

class TaskAlreadyAssignedError(Exception):
    pass

class TaskManager:
    def __init__(self):
        self._current_task: Task | None = None

    def assign_task(self, task: Task) -> None:
        if self._current_task is not None:
            raise TaskAlreadyAssignedError(
                f"Task {self._current_task.id} already assigned"
            )

        self._current_task = task
        self._current_task.status = TaskStatus.PENDING

    def get_task(self) -> Task | None:
        return self._current_task

    def has_task(self) -> bool:
        return self._current_task is not None

    def start_task(self):
        if self._current_task:
            self._current_task.status = TaskStatus.IN_PROGRESS

    def complete_task(self):
        if self._current_task:
            self._current_task.status = TaskStatus.DONE
            self._current_task = None

    def clear(self):
        self._current_task = None