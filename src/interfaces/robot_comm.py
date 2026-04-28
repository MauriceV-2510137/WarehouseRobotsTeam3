from abc import ABC, abstractmethod
from typing import Callable

from core.events import TaskReceivedEvent, AisleResponseEvent
from core.pose import Pose
from core.task import Task, TaskStatus

TaskCallback = Callable[[TaskReceivedEvent], None]
AisleCallback = Callable[[AisleResponseEvent], None]

class IRobotComm(ABC):

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def publish_heartbeat(self, task: Task | None, pose: Pose) -> None:
        pass

    @abstractmethod
    def publish_task_status(self, task_id: str, status: TaskStatus, reason: str | None = None) -> None:
        pass

    @abstractmethod
    def request_aisle(self, robot_id: str, aisle_id: str, task_id: str) -> None:
        pass

    @abstractmethod
    def release_aisle(self, robot_id: str, aisle_id: str) -> None:
        pass

    @abstractmethod
    def set_task_received_callback(self, callback: TaskCallback) -> None:
        pass

    @abstractmethod
    def set_aisle_response_callback(self, callback: AisleCallback) -> None:
        pass