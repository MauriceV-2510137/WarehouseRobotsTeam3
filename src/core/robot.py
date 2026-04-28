import random
from core.pose import Pose
from core.robot_model import RobotModel
from core.scheduler import Scheduler, ScheduledTask
from core.task_manager import TaskManager
from core.states.state_machine import StateMachine
from core.states.transition_id import TransitionID
from core.services.telemetry_service import TelemetryService
from core.odometry import OdometryEstimator
from core.navigator import Navigator
from core.event_queue import EventQueue

from interfaces.robot_comm import IRobotComm
from interfaces.sensors_controller import ISensorsController

class Robot:
    
    def __init__(self, motion, sensors : ISensorsController, comm : IRobotComm, model : RobotModel, initial_pose = None):
        self.motion = motion
        self.sensors = sensors
        self.comm = comm
        self._model = model

        self.pose = initial_pose or Pose()
        self.home  = (self.pose.x, self.pose.y)
        self.odometry = OdometryEstimator(model)
        self.odometry.reset(initial_pose)
        self.navigator = Navigator(model)

        self.task_manager = TaskManager()
        self.scheduler = Scheduler()

        self.telemetry = TelemetryService(self)    
        self.state_machine = StateMachine(self, initial_state=TransitionID.WAIT_CONNECTION)

        self.event_queue = EventQueue()

        self._collision_timer       = 0.0
        self._backoff_timer         = 0.0
        self._backoff_angular       = 0.0
        self._next_deadlock_timeout = random.uniform(1.0, 2.5)

        self._bind_events()
        self._setup_scheduler()
    
    # -------------------------
    # Wiring
    # -------------------------
    def _bind_events(self):
        self.comm.set_task_received_callback(self.event_queue.publish)
        self.comm.set_aisle_response_callback(self.event_queue.publish)

    def _setup_scheduler(self): # Heartbeat / health check
        heartbeat_task = ScheduledTask(interval_s=1.0, callback=self.telemetry.publish_heartbeat)
        self.scheduler.add(heartbeat_task)

    # -------------------------
    # Events
    # -------------------------
    def _process_events(self):
        for event in self.event_queue.poll_all():
            self.state_machine.handle_event(event)

    # -------------------------
    # Main loop
    # -------------------------
    def update(self, dt: float):
        self._update_pose()
        self._process_events()
        self.state_machine.update(dt)
        self.scheduler.update(dt)
    
    # -------------------------
    # Motion (with collision safety)
    # -------------------------

    _STOP_DISTANCE    = 0.25  # metres -- narrow cone (+-15 deg): full stop
    _SLOW_DISTANCE    = 0.50  # metres -- narrow cone (+-15 deg): start slowing
    _BUBBLE_DISTANCE  = 0.18  # metres -- 360 deg bubble: emergency stop
    _BACKOFF_DURATION = 1.2   # seconds of reversing to break deadlock

    def safe_move(self, linear: float, angular: float, dt: float = 0.0) -> None:
        """Two-zone collision avoidance with randomised deadlock backoff.

        Zone 1 - narrow cone (+-15 deg): slow down / stop for obstacles ahead.
        Zone 2 - 360 deg bubble at 0.18 m: emergency stop for robots that are
                 literally beside you.  Wall clearance in aisles is ~0.25 m so
                 the bubble never triggers on walls, only on other robots.
        Backoff: after a random timeout the robot reverses briefly with a random
                 rotation so the two robots end up at different positions."""
        if self._backoff_timer > 0:
            self._backoff_timer -= dt
            self.motion.move(-0.10, self._backoff_angular)
            return

        blocked = False
        if linear > 0:
            front = self.sensors.get_front_distance()
            if front <= self._STOP_DISTANCE:
                linear = 0.0
                blocked = True
            elif front < self._SLOW_DISTANCE:
                scale = (front - self._STOP_DISTANCE) / (self._SLOW_DISTANCE - self._STOP_DISTANCE)
                linear *= scale
            elif self.sensors.get_min_distance() <= self._BUBBLE_DISTANCE:
                linear = 0.0
                blocked = True

        if blocked:
            self._collision_timer += dt
            if self._collision_timer >= self._next_deadlock_timeout:
                self._collision_timer       = 0.0
                self._backoff_timer         = self._BACKOFF_DURATION
                left_dist  = self.sensors.get_left_distance()
                right_dist = self.sensors.get_right_distance()
                if max(left_dist, right_dist) < 0.5:
                    # Both walls close (narrow corridor): reverse straight, no rotation
                    self._backoff_angular = 0.0
                elif right_dist > left_dist:
                    self._backoff_angular = 0.8    # CCW → reverse curves toward open right side
                else:
                    self._backoff_angular = -0.8   # CW → reverse curves toward open left side
                self._next_deadlock_timeout = random.uniform(1.0, 2.5)
        else:
            self._collision_timer = 0.0

        self.motion.move(linear, angular)

    def reset_collision_state(self) -> None:
        """Call when entering a new navigation state so leftover backoff timers don't carry over."""
        self._collision_timer = 0.0
        self._backoff_timer   = 0.0

    # -------------------------
    # Sensors / pose
    # -------------------------
    def _update_pose(self):
        left_enc, right_enc = self.sensors.get_wheel_positions()
        heading = self.sensors.get_yaw() 
        self.pose = self.odometry.update(left_enc, right_enc, true_heading=heading)