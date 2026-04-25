from abc import ABC, abstractmethod
from core.task import Task

class IServerComm(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def assign_task(self, robot_id: str, task: Task):
        pass

    @abstractmethod
    def respond_aisle(self, robot_id: str, aisle_id: str, granted: bool):
        pass

    # --- inbound callbacks ---
    @abstractmethod
    def set_heartbeat_callback(self, cb):
        pass

    @abstractmethod
    def set_aisle_request_callback(self, cb):
        pass

    @abstractmethod
    def set_task_status_callback(self, cb):
        pass