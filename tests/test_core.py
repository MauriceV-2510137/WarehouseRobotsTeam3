# tests/test_core.py
import math
import pytest
from src.core.pose import Pose
from src.core.odometry import OdometryEstimator
from src.core.navigator import Navigator
from src.core.robot import Robot

# ─────────────────────────────────────────
# OdometryEstimator
# ─────────────────────────────────────────

class TestOdometryEstimator:

    def test_initial_pose_is_origin(self):
        odom = OdometryEstimator()
        pose = odom.update(0.0, 0.0, 0.0)
        assert pose.x == 0.0
        assert pose.y == 0.0
        assert pose.theta == 0.0

    def test_straight_line_forward(self):
        odom = OdometryEstimator()
        # Simulate both wheels rolling forward equally
        # One full wheel rotation = 2π * radius ≈ 0.207m of travel
        one_rotation = 2 * math.pi   # encoder radians
        pose = odom.update(one_rotation, one_rotation, yaw=0.0)
        assert pose.x == pytest.approx(0.207, abs=0.01)
        assert pose.y == pytest.approx(0.0,   abs=0.01)

    def test_heading_comes_from_compass_not_encoders(self):
        odom = OdometryEstimator()
        # Even if encoders are equal, heading should follow the compass
        pose = odom.update(1.0, 1.0, yaw=math.pi / 2)
        assert pose.theta == pytest.approx(math.pi / 2)

    def test_accumulated_position_over_steps(self):
        odom = OdometryEstimator()
        left_enc = right_enc = 0.0
        for _ in range(10):
            left_enc  += 0.5
            right_enc += 0.5
            pose = odom.update(left_enc, right_enc, yaw=0.0)
        # Should have moved forward, not sideways
        assert pose.x > 0.1
        assert abs(pose.y) < 0.01


# ─────────────────────────────────────────
# Navigator
# ─────────────────────────────────────────

class TestNavigator:

    def test_no_target_returns_zero(self):
        nav = Navigator()
        pose = Pose(x=0.0, y=0.0, theta=0.0)
        linear, angular = nav.compute(pose)
        assert linear == 0.0
        assert angular == 0.0

    def test_aligned_with_target_moves_forward(self):
        nav = Navigator()
        nav.set_target(1.0, 0.0)
        # Robot is at origin, facing right (theta=0), target is directly ahead
        pose = Pose(x=0.0, y=0.0, theta=0.0)
        linear, angular = nav.compute(pose)
        assert linear > 0.0    # should move forward
        assert abs(angular) < 0.1  # barely any turning needed

    def test_target_behind_robot_rotates_first(self):
        nav = Navigator()
        nav.set_target(-1.0, 0.0)  # target is directly behind
        pose = Pose(x=0.0, y=0.0, theta=0.0)
        linear, angular = nav.compute(pose)
        # Large angle error → should rotate, not drive forward
        assert linear == 0.0
        assert abs(angular) > 0.5

    def test_target_reached_clears_target(self):
        nav = Navigator()
        nav.set_target(0.05, 0.0)   # very close, within tolerance
        pose = Pose(x=0.0, y=0.0, theta=0.0)
        nav.compute(pose)
        assert nav.is_done()

    def test_is_done_when_no_target(self):
        nav = Navigator()
        assert nav.is_done()


# ─────────────────────────────────────────
# Robot — uses fakes, not real hardware
# ─────────────────────────────────────────

class FakeMotion:
    """Records what commands were sent."""
    def __init__(self):
        self.last_forward = None
        self.last_rotate  = None
        self.stopped      = False

    def move_forward(self, speed):
        self.last_forward = speed
        self.stopped = False

    def rotate(self, speed):
        self.last_rotate = speed
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeSensors:
    """Returns whatever values you configure."""
    def __init__(self):
        self.front    = 5.0   # no obstacle by default
        self.left     = 5.0
        self.right    = 5.0
        self.yaw      = 0.0
        self.left_enc = 0.0
        self.right_enc = 0.0

    def get_front_distance(self):   return self.front
    def get_left_distance(self):    return self.left
    def get_right_distance(self):   return self.right
    def get_yaw(self):              return self.yaw
    def get_wheel_positions(self):  return self.left_enc, self.right_enc


class TestRobot:

    def test_obstacle_in_front_causes_rotation(self):
        motion  = FakeMotion()
        sensors = FakeSensors()
        sensors.front = 0.2   # obstacle very close
        robot = Robot(motion, sensors)
        robot.update()
        assert motion.last_rotate is not None   # robot chose to rotate
        assert motion.last_forward is None      # did NOT drive forward

    def test_no_obstacle_no_target_stops(self):
        motion  = FakeMotion()
        sensors = FakeSensors()
        robot = Robot(motion, sensors)
        robot.update()
        assert motion.stopped

    def test_go_to_target_causes_forward_movement(self):
        motion  = FakeMotion()
        sensors = FakeSensors()
        robot = Robot(motion, sensors)
        robot.go_to(2.0, 0.0)   # target directly ahead
        robot.update()
        assert motion.last_forward is not None

    def test_obstacle_overrides_navigation(self):
        motion  = FakeMotion()
        sensors = FakeSensors()
        sensors.front = 0.2    # obstacle, even though we have a target
        robot = Robot(motion, sensors)
        robot.go_to(2.0, 0.0)
        robot.update()
        # Obstacle avoidance must win over navigation
        assert motion.last_rotate is not None
        assert motion.last_forward is None