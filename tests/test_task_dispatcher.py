"""
TaskDispatcher – dispatch logic tests.

Verifies FIFO ordering, nearest-robot selection, invalid task rejection,
and task cancellation. No MQTT or Webots dependency.
"""
import pytest
from unittest.mock import MagicMock

from server.core.task_dispatcher import TaskDispatcher
from server.core.task_store import TaskStore
from server.core.warehouse.warehouse_map import WarehouseMap
from server.core.registry.robot_registry import RobotRegistry
from server.core.registry.robot_record import RobotRecord
from server.core.registry.robot_server_status import RobotServerStatus
from core.pose import Pose
from core.task import TaskStatus


def make_dispatcher():
    comm = MagicMock()
    registry = MagicMock(spec=RobotRegistry)
    task_store = TaskStore()
    warehouse_map = WarehouseMap()
    dispatcher = TaskDispatcher(registry, task_store, comm, warehouse_map)
    return dispatcher, registry, task_store, comm


def idle_robot(robot_id: str, x: float = 0.0, y: float = 0.0) -> RobotRecord:
    r = RobotRecord(robot_id=robot_id)
    r.status = RobotServerStatus.IDLE
    r.pose = Pose(x, y, 0.0)
    return r


# ── Submission validation ────────────────────────────────────────────────────

def test_invalid_aisle_raises():
    dispatcher, *_ = make_dispatcher()
    with pytest.raises(ValueError):
        dispatcher.submit(aisle=0, shelf=1)


def test_invalid_shelf_raises():
    dispatcher, *_ = make_dispatcher()
    with pytest.raises(ValueError):
        dispatcher.submit(aisle=1, shelf=0)


def test_valid_submit_adds_to_store():
    dispatcher, _, task_store, _ = make_dispatcher()
    record = dispatcher.submit(aisle=1, shelf=1)
    assert task_store.get(record.task_id) is not None
    assert record.status == TaskStatus.PENDING


# ── Dispatch ─────────────────────────────────────────────────────────────────

def test_no_idle_robots_nothing_dispatched():
    dispatcher, registry, _, comm = make_dispatcher()
    registry.get_available.return_value = []
    dispatcher.submit(aisle=1, shelf=1)
    dispatcher.try_dispatch()
    comm.assign_task.assert_not_called()


def test_task_dispatched_to_idle_robot():
    dispatcher, registry, _, comm = make_dispatcher()
    robot = idle_robot("r1", x=0.0, y=4.0)
    registry.get_available.return_value = [robot]
    dispatcher.submit(aisle=1, shelf=1)
    dispatcher.try_dispatch()
    comm.assign_task.assert_called_once()
    args = comm.assign_task.call_args
    assert args[0][0] == "r1"


def test_nearest_robot_selected():
    """Two idle robots; the one closest to the aisle entry should be chosen."""
    dispatcher, registry, _, comm = make_dispatcher()

    # Aisle 1 entry is at (3.0, 4.0)
    far_robot   = idle_robot("far",   x=0.0, y=0.0)   # distance ≈ 5.0
    close_robot = idle_robot("close", x=3.0, y=3.0)   # distance ≈ 1.0

    registry.get_available.return_value = [far_robot, close_robot]
    dispatcher.submit(aisle=1, shelf=1)
    dispatcher.try_dispatch()

    assigned_id = comm.assign_task.call_args[0][0]
    assert assigned_id == "close"


def test_fifo_order_respected():
    """First submitted task should be dispatched first."""
    dispatcher, registry, task_store, comm = make_dispatcher()
    robot = idle_robot("r1", x=3.0, y=0.0)
    registry.get_available.return_value = [robot]

    r1 = dispatcher.submit(aisle=1, shelf=1)
    r2 = dispatcher.submit(aisle=2, shelf=1)

    dispatcher.try_dispatch()
    dispatched_id = comm.assign_task.call_args[0][1].id
    assert dispatched_id == r1.task_id


# ── Cancellation ─────────────────────────────────────────────────────────────

def test_pending_task_can_be_cancelled():
    dispatcher, registry, task_store, _ = make_dispatcher()
    registry.get_available.return_value = []
    record = dispatcher.submit(aisle=1, shelf=1)
    dispatcher.cancel(record.task_id)
    assert task_store.get(record.task_id).status == TaskStatus.REJECTED


def test_unknown_task_cancel_raises():
    dispatcher, *_ = make_dispatcher()
    with pytest.raises(ValueError):
        dispatcher.cancel("nonexistent")
