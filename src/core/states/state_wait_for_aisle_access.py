from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import AisleResponseEvent
from core.task import TaskStatus
from core.events import TaskReceivedEvent

class WaitingForAisleState(IRobotState):

    def __init__(self) -> None:
        self._transition : bool = False

    def on_enter(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return

        robot_id = robot.comm.robot_id
        aisle_id = task.aisle_id
        task_id = task.id

        robot.comm.request_aisle(
            robot_id=robot_id,
            aisle_id=aisle_id,
            task_id=task_id
        )

        robot.motion.stop()
        print(f"Waiting for aisle {aisle_id}")

    def on_exit(self, robot) -> None:
        self._transition = False

    def update(self, robot, dt: float) -> TransitionID:
        if self._transition:
            return TransitionID.MOVE_TO_SEGMENT
        return TransitionID.NO_TRANSITION
    
    def on_event(self, robot, event) -> None:
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")
        elif isinstance(event, AisleResponseEvent):
            if event.granted:
                self._transition = True