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
from core.collision.collision_manager import CollisionManager

from interfaces.robot_comm import IRobotComm
from interfaces.motion_controller import IMotionController
from interfaces.sensors_controller import ISensorsController


class Robot:

    def __init__(
        self,
        motion: IMotionController,
        sensors: ISensorsController,
        comm: IRobotComm,
        model: RobotModel,
        initial_pose: Pose | None = None
    ) -> None:

        self.motion = motion
        self.sensors = sensors
        self.comm = comm

        self.initial_pose: Pose = initial_pose if initial_pose else Pose()
        self.pose: Pose = Pose(self.initial_pose.x, self.initial_pose.y, self.initial_pose.theta)

        self.odometry = OdometryEstimator(model)
        self.odometry.reset(self.pose)

        self.navigator = Navigator(model)
        self.task_manager = TaskManager()
        self.scheduler = Scheduler()
        self.telemetry = TelemetryService(self)

        self.state_machine = StateMachine(self, initial_state=TransitionID.WAIT_CONNECTION)

        self.event_queue = EventQueue()

        self.collision = CollisionManager(self.sensors, self)

        self.aisle_lock_granted: bool = False

        self._bind_events()
        self._setup_scheduler()

    @property
    def priority(self) -> int:
        return hash(self.comm.robot_id) % 1000

    def _bind_events(self) -> None:
        self.comm.set_task_received_callback(self.event_queue.publish)
        self.comm.set_aisle_response_callback(self.event_queue.publish)

    def _setup_scheduler(self) -> None:
        heartbeat_task = ScheduledTask(
            interval_s=0.5,
            callback=self.telemetry.publish_heartbeat
        )
        self.scheduler.add(heartbeat_task)

    def _process_events(self) -> None:
        for event in self.event_queue.poll_all():
            self.state_machine.handle_event(event)

    def _update_pose(self) -> None:
        left_enc, right_enc = self.sensors.get_wheel_positions()
        heading = self.sensors.get_yaw()
        self.pose = self.odometry.update(left_enc, right_enc, true_heading=heading)

    def update(self, dt: float) -> None:
        self._update_pose()
        self._process_events()

        self.state_machine.update(dt)
        self.scheduler.update(dt)