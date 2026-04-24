import random
from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import TaskReceivedEvent
from core.task import TaskStatus

class PickingItemState(IRobotState):

    def __init__(self):
        self.wait_duration = 0.0
        self.elapsed = 0.0

    def on_enter(self, robot) -> None:
        self.wait_duration = random.uniform(5, 10)
        self.elapsed = 0.0
        robot.motion.stop()
        print("Picking item...")

    def on_exit(self, robot):
        self.elapsed = 0.0

    def update(self, robot, dt: float) -> TransitionID:
        self.elapsed += dt

        if self.elapsed >= self.wait_duration:
            return TransitionID.MOVE_TO_BASE

        return TransitionID.NO_TRANSITION

    def on_event(self, robot, event):
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")