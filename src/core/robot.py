from core.odometry import OdometryEstimator
from core.navigator import Navigator
from core.task_manager import TaskManager, TaskAlreadyAssignedError
from core.events import TaskReceivedEvent, AisleResponseEvent
from core.state_machine import StateMachine
from core.states.state_waiting_for_connection import WaitingForConnectionState

from interfaces.motion_controller import IMotionController
from interfaces.sensors_controller import ISensorsController
from interfaces.robot_comm import IRobotComm

class Robot:
    def __init__(self, motion_controller: IMotionController, sensors: ISensorsController, comm: IRobotComm):
        self.motion    = motion_controller
        self.sensors   = sensors

        self.comm = comm
        self.comm.set_on_task_received(self._on_task_received)
        self.comm.set_on_aisle_response(self._on_aisle_response)
        
        self.odometry  = OdometryEstimator()
        self.navigator = Navigator()

        self.task_manager = TaskManager()
        
        self.pose = None
        self.state_machine = StateMachine(self, WaitingForConnectionState())
    
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
    # Main loop
    # -------------------------
    def update(self):

        # Update pose
        self._update_pose()

        # Update state machine
        self.state_machine.update()

        # Send current status
        if self.comm.is_connected():
            task = self.task_manager.get_task()
            self.comm.publish_heartbeat(task, self.pose)