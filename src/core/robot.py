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

        self.pose = initial_pose or Pose()
        self.odometry = OdometryEstimator(model)
        self.odometry.reset(initial_pose)
        self.navigator = Navigator(model)

        self.task_manager = TaskManager()
        self.scheduler = Scheduler()

        self.telemetry = TelemetryService(self)    
        self.state_machine = StateMachine(self, initial_state=TransitionID.WAIT_CONNECTION)

        self.event_queue = EventQueue()

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
    # Sensors / pose
    # -------------------------
    def _update_pose(self):
        left_enc, right_enc = self.sensors.get_wheel_positions()
        heading = self.sensors.get_yaw() 
        self.pose = self.odometry.update(left_enc, right_enc, true_heading=heading)