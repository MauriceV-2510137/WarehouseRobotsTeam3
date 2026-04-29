from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import AisleResponseEvent, TaskReceivedEvent
from core.task import TaskStatus

class WaitingForAisleState(IRobotState):

    def __init__(self) -> None:
        self._granted = False

    def on_enter(self, robot) -> None:
        self._granted = False
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        if self._granted:
            return TransitionID.MOVE_TO_AISLE
        return TransitionID.NO_TRANSITION

    def on_event(self, robot, event) -> None:

        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(
                event.task.id,
                TaskStatus.REJECTED,
                reason="Robot already has active task"
            )

        elif isinstance(event, AisleResponseEvent):

            if event.granted:
                self._granted = True
                robot.aisle_lock_granted = True

            else:
                task = robot.task_manager.get_task()
                if task:
                    robot.comm.request_aisle(
                        robot_id=robot.comm.robot_id,
                        aisle_id=task.aisle_id,
                        task_id=task.id
                    )