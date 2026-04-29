"""
CollisionManager – safety state tests.

Verifies SAFE / EVADE / STOP transitions and velocity modifications,
without any Webots dependency.
"""
import pytest
from unittest.mock import MagicMock
from core.collision.collision_manager import CollisionManager, SafetyState


def make_manager(front_distance: float) -> CollisionManager:
    sensors = MagicMock()
    sensors.get_front_distance.return_value = front_distance
    return CollisionManager(sensors)


DT = 0.1   # seconds per tick


# ── SAFE ─────────────────────────────────────────────────────────────────────

def test_clear_path_is_safe():
    mgr = make_manager(1.0)
    mgr.apply(0.2, 0.0, DT)
    assert mgr.get_state() == SafetyState.SAFE


def test_safe_state_does_not_modify_velocities():
    mgr = make_manager(1.0)
    linear, angular = mgr.apply(0.2, 0.5, DT)
    assert linear  == pytest.approx(0.2)
    assert angular == pytest.approx(0.5)


# ── STOP ─────────────────────────────────────────────────────────────────────

def test_critically_close_obstacle_triggers_stop():
    mgr = make_manager(0.05)   # below _STOP_DIST (0.15 m)
    mgr.apply(0.2, 0.0, DT)
    assert mgr.get_state() == SafetyState.STOP


def test_stop_state_zeroes_velocities():
    mgr = make_manager(0.05)
    linear, angular = mgr.apply(0.2, 0.5, DT)
    assert linear  == pytest.approx(0.0)
    assert angular == pytest.approx(0.0)


# ── EVADE ────────────────────────────────────────────────────────────────────

def test_approaching_obstacle_triggers_evade():
    """Simulate closing gap: first reading far, then nearer → approaching."""
    sensors = MagicMock()
    readings = iter([0.40, 0.30])          # closing at 0.10 m per tick
    sensors.get_front_distance.side_effect = lambda: next(readings)

    mgr = CollisionManager(sensors)
    mgr.apply(0.2, 0.0, DT)               # seed prev_front = 0.40
    mgr.apply(0.2, 0.0, DT)               # 0.30 < 0.50 and approaching
    assert mgr.get_state() == SafetyState.EVADE


def test_evade_caps_linear_speed():
    sensors = MagicMock()
    readings = iter([0.40, 0.30])
    sensors.get_front_distance.side_effect = lambda: next(readings)

    mgr = CollisionManager(sensors)
    mgr.apply(0.2, 0.0, DT)
    linear, _ = mgr.apply(0.2, 0.0, DT)
    assert linear <= 0.04 + 1e-9           # _EVADE_LINEAR_MAX


def test_evade_adds_left_turn_bias():
    sensors = MagicMock()
    readings = iter([0.40, 0.30])
    sensors.get_front_distance.side_effect = lambda: next(readings)

    mgr = CollisionManager(sensors)
    mgr.apply(0.0, 0.0, DT)
    _, angular = mgr.apply(0.0, 0.0, DT)
    assert angular > 0.0                   # left-turn bias added


# ── Forced evasion window ────────────────────────────────────────────────────

def test_stop_forces_evasion_window_afterwards():
    """After a STOP, the robot must remain in EVADE even if obstacle clears."""
    sensors = MagicMock()
    # First tick: critically close → STOP; subsequent ticks: clear
    readings = [0.05] + [1.0] * 10
    sensors.get_front_distance.side_effect = readings.__getitem__
    call_count = [0]

    def get_distance():
        v = readings[call_count[0]]
        call_count[0] += 1
        return v

    sensors.get_front_distance.side_effect = get_distance

    mgr = CollisionManager(sensors)
    mgr.apply(0.2, 0.0, DT)               # STOP
    mgr.apply(0.2, 0.0, DT)               # path clear but window still active
    assert mgr.get_state() == SafetyState.EVADE


# ── is_stop / is_yield helpers ───────────────────────────────────────────────

def test_is_stop_true_when_stopped():
    mgr = make_manager(0.05)
    mgr.apply(0.2, 0.0, DT)
    assert mgr.is_stop()


def test_is_yield_true_when_stopped():
    mgr = make_manager(0.05)
    mgr.apply(0.2, 0.0, DT)
    assert mgr.is_yield()
