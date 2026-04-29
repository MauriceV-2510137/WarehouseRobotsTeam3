"""
OdometryEstimator – sensor fusion tests.

Verifies dead-reckoning accuracy and compass override, without any
Webots dependency.
"""
import math
import pytest
from core.odometry import OdometryEstimator
from core.robot_model import RobotModel
from core.pose import Pose

MODEL = RobotModel(
    wheel_radius=0.033,
    wheel_base=0.160,
    max_wheel_speed=6.28,
    max_linear_speed=0.20,
    max_angular_speed=1.5,
)

WHEEL_RADIUS = MODEL.wheel_radius
WHEEL_BASE   = MODEL.wheel_base


def make_odometry(start: Pose | None = None) -> OdometryEstimator:
    odo = OdometryEstimator(MODEL)
    odo.reset(start or Pose())
    return odo


# ── Initialisation ───────────────────────────────────────────────────────────

def test_first_update_returns_initial_pose():
    odo = make_odometry(Pose(1.0, 2.0, 0.5))
    pose = odo.update(0.0, 0.0)
    assert pose.x == pytest.approx(1.0)
    assert pose.y == pytest.approx(2.0)
    assert pose.theta == pytest.approx(0.5)


# ── Straight-line motion ─────────────────────────────────────────────────────

def test_straight_forward_one_revolution():
    """One full wheel revolution should advance the robot by 2πr metres."""
    odo = make_odometry()
    circumference = 2 * math.pi * WHEEL_RADIUS  # ≈ 0.2073 m

    odo.update(0.0, 0.0)                         # seed encoders
    pose = odo.update(circumference / WHEEL_RADIUS,
                      circumference / WHEEL_RADIUS)

    assert pose.x == pytest.approx(circumference, abs=1e-6)
    assert pose.y == pytest.approx(0.0, abs=1e-6)
    assert pose.theta == pytest.approx(0.0, abs=1e-6)


def test_straight_motion_no_y_drift():
    """Driving straight should not change y when starting at theta=0."""
    odo = make_odometry()
    odo.update(0.0, 0.0)
    for _ in range(10):
        odo.update(odo._prev_left + 0.01, odo._prev_right + 0.01)
    assert odo.pose.y == pytest.approx(0.0, abs=1e-9)


# ── Rotation ─────────────────────────────────────────────────────────────────

def test_spin_in_place_90_degrees():
    """Right wheel forward, left wheel backward by equal arcs → rotate in place."""
    odo = make_odometry()
    arc = (math.pi / 2) * (WHEEL_BASE / 2)   # arc for 90° spin
    enc = arc / WHEEL_RADIUS

    odo.update(0.0, 0.0)
    pose = odo.update(-enc, enc)

    assert pose.x == pytest.approx(0.0, abs=1e-6)
    assert pose.y == pytest.approx(0.0, abs=1e-6)
    assert pose.theta == pytest.approx(math.pi / 2, abs=1e-6)


# ── Compass fusion ───────────────────────────────────────────────────────────

def test_compass_overrides_dead_reckoned_heading():
    odo = make_odometry()
    odo.update(0.0, 0.0)
    # Move slightly while providing a different compass heading
    pose = odo.update(0.1, 0.1, true_heading=1.23)
    assert pose.theta == pytest.approx(1.23)


def test_no_compass_uses_dead_reckoning():
    odo = make_odometry()
    odo.update(0.0, 0.0)
    enc = 0.1 / WHEEL_RADIUS
    pose = odo.update(-enc, enc)           # spin; no compass
    assert pose.theta != pytest.approx(0.0)
