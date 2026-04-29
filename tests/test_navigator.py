"""
Navigator – proportional controller tests.

Verifies that the Navigator produces correct velocities and correctly
detects arrival, without any Webots dependency.
"""
import math
import pytest
from core.navigator import Navigator
from core.robot_model import RobotModel
from core.pose import Pose

MODEL = RobotModel(
    wheel_radius=0.033,
    wheel_base=0.160,
    max_wheel_speed=6.28,
    max_linear_speed=0.20,
    max_angular_speed=1.5,
)


def make_navigator() -> Navigator:
    return Navigator(MODEL)


# ── Idle behaviour ──────────────────────────────────────────────────────────

def test_no_target_returns_zero():
    nav = make_navigator()
    linear, angular = nav.compute(Pose(0, 0, 0))
    assert linear == 0.0
    assert angular == 0.0


# ── Arrival detection ───────────────────────────────────────────────────────

def test_arrival_within_tolerance():
    nav = make_navigator()
    nav.set_target(0.01, 0.0)              # 0.01 m < 0.02 m tolerance
    linear, angular = nav.compute(Pose(0, 0, 0))
    assert linear == 0.0
    assert angular == 0.0
    assert nav.reached_target()


def test_no_arrival_outside_tolerance():
    nav = make_navigator()
    nav.set_target(1.0, 0.0)
    nav.compute(Pose(0, 0, 0))
    assert not nav.reached_target()


def test_clear_reached_resets_flag():
    nav = make_navigator()
    nav.set_target(0.0, 0.0)
    nav.compute(Pose(0, 0, 0))
    assert nav.reached_target()
    nav.clear_reached()
    assert not nav.reached_target()


# ── Direction ───────────────────────────────────────────────────────────────

def test_aligned_with_target_produces_positive_linear():
    nav = make_navigator()
    nav.set_target(1.0, 0.0)
    linear, angular = nav.compute(Pose(0, 0, 0))   # facing right, target is right
    assert linear > 0.0
    assert abs(angular) < 1e-6


def test_target_behind_robot_rotates_in_place():
    """When angle error > 0.8 rad the robot should rotate in place (linear = 0)."""
    nav = make_navigator()
    nav.set_target(-1.0, 0.0)             # target is directly behind robot
    linear, angular = nav.compute(Pose(0, 0, 0))
    assert linear == 0.0
    assert abs(angular) > 0.0


def test_target_left_produces_positive_angular():
    """Target 90° to the left should produce a positive (CCW) angular velocity."""
    nav = make_navigator()
    nav.set_target(0.0, 1.0)             # directly to the left
    _, angular = nav.compute(Pose(0, 0, 0))
    assert angular > 0.0


# ── Speed limits ─────────────────────────────────────────────────────────────

def test_linear_speed_capped():
    nav = make_navigator()
    nav.set_target(100.0, 0.0)           # very far away → would exceed limit
    linear, _ = nav.compute(Pose(0, 0, 0))
    assert linear <= MODEL.max_linear_speed


def test_angular_speed_capped():
    nav = make_navigator()
    nav.set_target(0.0, 100.0)
    _, angular = nav.compute(Pose(0, 0, 0))
    assert abs(angular) <= MODEL.max_angular_speed
