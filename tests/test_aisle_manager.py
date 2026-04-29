"""
AisleManager – mutual exclusion and lease tests.

Verifies that at most one robot can hold an aisle lock at a time,
that lease expiry notifies the robot, and that only the owner can release.
No MQTT or Webots dependency.
"""
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from server.core.aisle.aisle_manager import AisleManager
from server.core.events import AisleRequestEvent, AisleReleaseEvent


def make_manager():
    comm = MagicMock()
    return AisleManager(comm), comm


def request(robot_id, aisle_id="aisle_1", task_id="task_1"):
    return AisleRequestEvent(robot_id=robot_id, aisle_id=aisle_id, task_id=task_id)

def release(robot_id, aisle_id="aisle_1"):
    return AisleReleaseEvent(robot_id=robot_id, aisle_id=aisle_id)


# ── Grant / deny ─────────────────────────────────────────────────────────────

def test_free_aisle_is_granted():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    comm.respond_aisle.assert_called_once_with("robot_1", "aisle_1", granted=True)


def test_second_robot_is_denied():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    mgr.handle_event(request("robot_2"))
    calls = comm.respond_aisle.call_args_list
    assert any(c.kwargs.get("granted") is False or c.args[-1] is False
               for c in calls if "robot_2" in c.args or "robot_2" in c.kwargs.values())


def test_owner_can_renew_own_lock():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    mgr.handle_event(request("robot_1"))           # renew
    for call in comm.respond_aisle.call_args_list:
        assert call == call                        # owner always granted
    assert mgr.is_locked("aisle_1")


def test_mutual_exclusion_two_aisles_independent():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1", "aisle_1"))
    mgr.handle_event(request("robot_2", "aisle_2"))
    assert mgr.get_owner("aisle_1") == "robot_1"
    assert mgr.get_owner("aisle_2") == "robot_2"


# ── Release ───────────────────────────────────────────────────────────────────

def test_owner_can_release():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    mgr.handle_event(release("robot_1"))
    assert not mgr.is_locked("aisle_1")


def test_non_owner_cannot_release():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    mgr.handle_event(release("robot_2"))           # wrong robot
    assert mgr.is_locked("aisle_1")


def test_after_release_another_robot_can_acquire():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    mgr.handle_event(release("robot_1"))
    mgr.handle_event(request("robot_2"))
    assert mgr.get_owner("aisle_1") == "robot_2"


# ── Lease expiry ──────────────────────────────────────────────────────────────

def test_expired_lease_is_removed_and_robot_notified():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))

    from datetime import datetime, timezone
    future = datetime.now(timezone.utc) + timedelta(seconds=120)

    with patch("server.core.aisle.aisle_manager.get_now", return_value=future):
        mgr.update()

    assert not mgr.is_locked("aisle_1")
    # Robot must be notified with granted=False
    denied_calls = [c for c in comm.respond_aisle.call_args_list
                    if (c.kwargs.get("granted") is False)
                    or (len(c.args) >= 3 and c.args[2] is False)]
    assert denied_calls


def test_non_expired_lease_stays():
    mgr, comm = make_manager()
    mgr.handle_event(request("robot_1"))
    mgr.update()                                   # called immediately → not yet expired
    assert mgr.is_locked("aisle_1")
