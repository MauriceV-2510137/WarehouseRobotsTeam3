from abc import ABC, abstractmethod
from typing import Callable

from core.task import Task
from server.core.events import HeartbeatEvent, TaskStatusEvent, AisleRequestEvent, AisleReleaseEvent

HeartbeatCallback = Callable[[HeartbeatEvent], None]
TaskStatusCallback = Callable[[TaskStatusEvent], None]
AisleRequestCallback = Callable[[AisleRequestEvent], None]
AisleReleaseCallback = Callable[[AisleReleaseEvent], None]

class IServerComm(ABC):

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
    def assign_task(self, robot_id: str, task: Task) -> None:
        pass

    @abstractmethod
    def respond_aisle(self, robot_id: str, aisle_id: str, granted: bool) -> None:
        pass

    # --- inbound callbacks ---
    @abstractmethod
    def set_heartbeat_callback(self, cb: HeartbeatCallback) -> None:
        pass

    @abstractmethod
    def set_task_status_callback(self, cb: TaskStatusCallback) -> None:
        pass

    @abstractmethod
    def set_aisle_request_callback(self, cb: AisleRequestCallback) -> None:
        pass

    @abstractmethod
    def set_aisle_release_callback(self, cb: AisleReleaseCallback) -> None:
        pass