from abc import ABC, abstractmethod
from typing import Callable

from core.events import TaskReceivedEvent, AisleResponseEvent
from core.pose import Pose
from core.task import Task

TaskCallback = Callable[[TaskReceivedEvent], None]
AisleCallback = Callable[[AisleResponseEvent], None]

class IRobotComm(ABC):

    @abstractmethod
    def publish_task_status(self, task_id: str, status: str, reason: str | None = None):
        pass

    @abstractmethod
    def request_aisle(self, robot_id: str, aisle_id: str, task_id: str):
        pass

    @abstractmethod
    def publish_heartbeat(self, task: Task | None, pose: Pose):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def set_on_task_received(self, callback: TaskCallback) -> None:
        pass

    @abstractmethod
    def set_on_aisle_response(self, callback: AisleCallback) -> None:
        pass