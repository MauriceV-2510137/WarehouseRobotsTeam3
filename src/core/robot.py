from core.odometry import OdometryEstimator
from core.navigator import Navigator
from core.task_manager import TaskManager, TaskAlreadyAssignedError
from core.events import TaskReceivedEvent, AisleResponseEvent
from core.state_machine import StateMachine
from core.states.state_waiting_for_connection import WaitingForConnectionState
from core.scheduler import Scheduler, ScheduledTask
from core.services.telemetry_service import TelemetryService

from interfaces.motion_controller import IMotionController
from interfaces.sensors_controller import ISensorsController
from interfaces.robot_comm import IRobotComm
from core.states.state_idle import IdleState
from core.task_manager import TaskManager
from core.aisle_manager import AisleManager
from core.pose import Pose

class Robot:

    def _handleStartup(self):
        self.comm.set_on_task_received(self._on_task_received)
        self.comm.set_on_aisle_response(self._on_aisle_response)

        self.scheduler.add(ScheduledTask(
            interval_s= 1,
            callback= self.telemetry.publish_heartbeat
        ))
    
    def __init__(self, timestep, motion_controller: IMotionController, sensors: ISensorsController, comm: IRobotComm):
        self.timestep = timestep
        self.sim_time = 0.0

        self.scheduler = Scheduler()

        self.telemetry = TelemetryService(self)

        self.motion = motion_controller
        self.sensors = sensors
        self.comm = comm
        
        self.odometry = OdometryEstimator()
        self.navigator = Navigator()

        self.task_manager = TaskManager()
        
        self.pose = None
        self.state_machine = StateMachine(self, IdleState())
        self.task_manager = TaskManager()
        self.aisle_manager = AisleManager(3) 
        self.robot_id = 0
        
        # Initialize pose to prevent None errors
        self.pose = Pose(0.0, 0.0, 0.0)
        self.current_state = IdleState()
        self.current_state.on_enter(self)

        self._handleStartup()
    
    # -------------------------
    # Event handlers
    # -------------------------
    def _on_task_received(self, event: TaskReceivedEvent):
        try:
            self.task_manager.assign_task(event.task)
        except TaskAlreadyAssignedError:
            self.comm.publish_task_status(event.task.id, "rejected", reason="robot_busy")

    def _on_aisle_response(self, event: AisleResponseEvent):
        if event.granted:
            pass
            # Allow aisle access here
        else:
            pass
            # Cant go in aisle

    
    # -------------------------
    # Sensors / pose
    # -------------------------
    def _update_pose(self):
        left_enc, right_enc = self.sensors.get_wheel_positions()
        yaw  = self.sensors.get_yaw()
        self.pose = self.odometry.update(left_enc, right_enc, yaw)
    
    # -------------------------
    # Simulation Time
    # -------------------------
    
    def _update_sim_time(self):
        self.sim_time += self.timestep / 1000.0
    
    # -------------------------
    # Main loop
    # -------------------------
    def update(self):

        # Update simulation time
        self._update_sim_time()

        # FAST Loop
        self._update_pose()
        self.state_machine.update()

        # Scheduled Loop
        self.scheduler.update(self.sim_time)