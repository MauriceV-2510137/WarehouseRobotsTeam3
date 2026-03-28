"""
Tests for warehouse components.

Run with:   pytest tests/
"""

import asyncio
import math
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ── Navigation tests (no Webots needed) ─────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'robots'))

from navigation import Navigator, Pose


class FakeMotor:
    def __init__(self): self.velocity = 0.0
    def setVelocity(self, v): self.velocity = v


def make_navigator():
    left, right = FakeMotor(), FakeMotor()
    nav = Navigator(left, right, max_speed=6.28)
    return nav, left, right


class TestNavigator:
    def test_stop_when_at_goal(self):
        nav, left, right = make_navigator()
        at_goal = nav.drive_to(Pose(1.0, 1.0, 0.0), Pose(1.0, 1.0, 0.0))
        assert at_goal is True
        assert left.velocity == 0.0
        assert right.velocity == 0.0

    def test_not_at_goal_when_far(self):
        nav, left, right = make_navigator()
        at_goal = nav.drive_to(Pose(0.0, 0.0, 0.0), Pose(5.0, 0.0, 0.0))
        assert at_goal is False

    def test_moves_toward_target(self):
        """Robot should set positive velocities when driving forward."""
        nav, left, right = make_navigator()
        # Robot at origin, facing right (theta=0), target straight ahead
        nav.drive_to(Pose(0.0, 0.0, 0.0), Pose(2.0, 0.0, 0.0))
        assert left.velocity > 0
        assert right.velocity > 0

    def test_rotates_for_large_angle_error(self):
        """With big angle error, one wheel should go backward (rotation in place)."""
        nav, left, right = make_navigator()
        # Robot facing right, target is directly behind
        nav.drive_to(Pose(0.0, 0.0, 0.0), Pose(-2.0, 0.0, 0.0))
        # Rotation in place → wheels have opposite signs
        assert left.velocity * right.velocity < 0

    def test_normalize_angle(self):
        assert abs(Navigator._normalize_angle(math.pi + 0.1) - (-math.pi + 0.1)) < 1e-9
        assert abs(Navigator._normalize_angle(-math.pi - 0.1) - (math.pi - 0.1)) < 1e-9
        assert Navigator._normalize_angle(0.5) == pytest.approx(0.5)

    def test_speed_clamp(self):
        nav, left, right = make_navigator()
        nav.drive_to(Pose(0.0, 0.0, 0.0), Pose(100.0, 0.0, 0.0))
        assert abs(left.velocity)  <= nav.max_speed
        assert abs(right.velocity) <= nav.max_speed


# ── Server logic tests ───────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

import importlib
# We import the module but patch WebSocket-related parts so no real server starts
import main as srv


@pytest.fixture(autouse=True)
def reset_state():
    """Reset all global server state before each test."""
    srv.task_queue.clear()
    srv.robots.clear()
    srv.aisle_locks.clear()
    srv.robot_connections.clear()
    srv.ui_connections.clear()
    yield


class TestTaskQueue:
    def test_make_task_generates_unique_ids(self):
        t1 = srv.make_task("Widget A", 0, 0)
        t2 = srv.make_task("Widget A", 0, 0)
        assert t1.task_id != t2.task_id

    def test_make_task_fields(self):
        t = srv.make_task("Bolt", 2, 1)
        assert t.item_name == "Bolt"
        assert t.aisle == 2
        assert t.shelf == 1
        assert t.assigned_to is None


class TestAisleLocks:
    @pytest.mark.asyncio
    async def test_aisle_granted_when_free(self):
        srv.robots["r0"] = srv.RobotState("r0", status=srv.RobotStatus.MOVING_TO_SHELF)
        ws_mock = AsyncMock()
        srv.robot_connections["r0"] = ws_mock

        await srv.handle_request_aisle("r0", 1)

        assert srv.aisle_locks[1] == "r0"
        ws_mock.send_text.assert_called_once()
        sent = ws_mock.send_text.call_args[0][0]
        assert "aisle_granted" in sent

    @pytest.mark.asyncio
    async def test_aisle_denied_when_occupied(self):
        srv.robots["r0"] = srv.RobotState("r0")
        srv.robots["r1"] = srv.RobotState("r1", status=srv.RobotStatus.MOVING_TO_SHELF)
        srv.aisle_locks[0] = "r0"
        ws_mock = AsyncMock()
        srv.robot_connections["r1"] = ws_mock

        await srv.handle_request_aisle("r1", 0)

        assert srv.aisle_locks[0] == "r0"   # unchanged
        assert srv.robots["r1"].status == srv.RobotStatus.WAITING_FOR_AISLE
        sent = ws_mock.send_text.call_args[0][0]
        assert "aisle_denied" in sent

    @pytest.mark.asyncio
    async def test_release_aisle(self):
        srv.robots["r0"] = srv.RobotState("r0")
        srv.robots["r0"].aisle_reserved = 2
        srv.aisle_locks[2] = "r0"

        await srv.handle_release_aisle("r0", 2)

        assert 2 not in srv.aisle_locks
        assert srv.robots["r0"].aisle_reserved is None


class TestDispatch:
    @pytest.mark.asyncio
    async def test_task_dispatched_to_idle_robot(self):
        srv.robots["r0"] = srv.RobotState("r0", status=srv.RobotStatus.IDLE)
        ws_mock = AsyncMock()
        srv.robot_connections["r0"] = ws_mock
        task = srv.make_task("Gear", 1, 0)
        srv.task_queue.append(task)

        await srv.dispatch_tasks()

        assert len(srv.task_queue) == 0
        assert srv.robots["r0"].status == srv.RobotStatus.MOVING_TO_SHELF
        ws_mock.send_text.assert_called_once()
        sent = ws_mock.send_text.call_args[0][0]
        assert "assign_task" in sent

    @pytest.mark.asyncio
    async def test_no_dispatch_when_no_idle_robots(self):
        srv.robots["r0"] = srv.RobotState("r0", status=srv.RobotStatus.PICKING)
        task = srv.make_task("Gear", 1, 0)
        srv.task_queue.append(task)

        await srv.dispatch_tasks()

        assert len(srv.task_queue) == 1   # still in queue
        assert srv.robots["r0"].status == srv.RobotStatus.PICKING

    @pytest.mark.asyncio
    async def test_multiple_tasks_multiple_robots(self):
        for i in range(3):
            srv.robots[f"r{i}"] = srv.RobotState(f"r{i}", status=srv.RobotStatus.IDLE)
            srv.robot_connections[f"r{i}"] = AsyncMock()
        for i in range(3):
            srv.task_queue.append(srv.make_task(f"item{i}", i, 0))

        await srv.dispatch_tasks()

        assert len(srv.task_queue) == 0
        for i in range(3):
            assert srv.robots[f"r{i}"].status == srv.RobotStatus.MOVING_TO_SHELF
