import math
import uuid
from collections import deque

from server.core.time_utils import get_now

from core.task import Task, TaskStatus
from server.core.registry.robot_record import RobotRecord
from server.core.registry.robot_registry import RobotRegistry
from server.core.registry.robot_server_status import RobotServerStatus
from server.core.task_store import TaskRecord, TaskStore
from server.core.warehouse.warehouse_map import WarehouseMap

from server.interfaces.server_comm import IServerComm

class TaskDispatcher:
    def __init__(self, registry: RobotRegistry, task_store: TaskStore, comm: IServerComm, warehouse_map: WarehouseMap) -> None:
        self._registry = registry
        self._task_store = task_store
        self._comm = comm
        self._map = warehouse_map
        self._queue: deque[TaskRecord] = deque()

    def submit(self, aisle: int, shelf: int) -> TaskRecord:
        self._map.resolve(aisle, shelf)  # validates; raises ValueError on bad input

        task_id = uuid.uuid4().hex[:8]
        record = TaskRecord(task_id=task_id, aisle=aisle, shelf=shelf)
        self._task_store.add(record)
        self._queue.append(record)
        return record

    def cancel(self, task_id: str) -> None:
        record = self._task_store.get(task_id)
        if record is None:
            raise ValueError(f"Task '{task_id}' not found")

        # atomic intent: only cancel if still in queue
        if record not in self._queue:
            raise ValueError(f"Task '{task_id}' already dispatched")

        self._queue.remove(record)

        record.status = TaskStatus.REJECTED
        record.updated_at = get_now()

    def try_dispatch(self) -> None:
        if not self._queue:
            return

        idle_robots = self._registry.get_available()
        if not idle_robots:
            return

        record = self._queue.popleft()
        location = self._map.resolve(record.aisle, record.shelf)

        robot = _closest_robot(idle_robots, location.aisle_pos)

        task = Task(
            id=record.task_id,
            aisle_id=f"aisle_{record.aisle}",
            aisle_pos=list(location.aisle_pos),
            segment_pos=list(location.segment_pos),
        )

        record.robot_id = robot.robot_id
        record.status = TaskStatus.IN_PROGRESS
        record.updated_at = get_now()
        
        robot.status = RobotServerStatus.BUSY  # optimistic update; corrected by tracker on next heartbeat

        self._comm.assign_task(robot.robot_id, task)

def _closest_robot(robots: list[RobotRecord], target: tuple[float, float]) -> RobotRecord:
    tx, ty = target
    return min(robots, key=lambda r: math.hypot(r.pose.x - tx, r.pose.y - ty))