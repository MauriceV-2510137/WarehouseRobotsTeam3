from core.pose import Pose
from core.scheduler import Scheduler, ScheduledTask
from core.task_manager import TaskManager
from core.states.state_machine import StateMachine
from core.states.state_waiting_for_connection import WaitingForConnectionState
from core.services.telemetry_service import TelemetryService
from core.odometry import OdometryEstimator
from core.navigator import Navigator

class Robot:
    
    def __init__(self, motion, sensors, comm, model):
        self.motion = motion
        self.sensors = sensors
        self.comm = comm
        self.model = model

        self.pose = Pose()
        self.odometry = OdometryEstimator(model)
        self.navigator = Navigator(model)

        self.task_manager = TaskManager()
        self.scheduler = Scheduler()

        self.telemetry = TelemetryService(self)    
        
        self.state_machine = StateMachine(self, WaitingForConnectionState())

        self._bind_events()
        self._setup_scheduler()
    
    # -------------------------
    # Wiring
    # -------------------------
    def _bind_events(self):
        self.comm.set_on_task_received(self._on_task_received)
        self.comm.set_on_aisle_response(self._on_aisle_response)

    def _setup_scheduler(self):
        # Heartbeat / health check
        self.scheduler.add(
            ScheduledTask(
                interval_s=1.0,
                callback=self.telemetry.publish_heartbeat
            )
        )

    # -------------------------
    # Main loop
    # -------------------------
    def update(self, dt: float):
        self._update_pose()
        self.state_machine.update(dt)
        self.scheduler.update(dt)
    
    # -------------------------
    # Event handlers
    # -------------------------
    def _on_task_received(self, event):
        self.task_manager.assign_task(event.task)
            
    def _on_aisle_response(self, event):
        pass
    
    # -------------------------
    # Sensors / pose
    # -------------------------
    def _update_pose(self):
        left_enc, right_enc = self.sensors.get_wheel_positions()
        self.pose = self.odometry.update(left_enc, right_enc)