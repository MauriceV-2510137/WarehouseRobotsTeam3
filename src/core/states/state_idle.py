from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import TaskReceivedEvent
from core.task import TaskStatus, TaskAlreadyAssignedError


class IdleState(IRobotState):

    def on_enter(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        if robot.task_manager.has_task():
            return TransitionID.WAIT_FOR_AISLE_ACCESS
        return TransitionID.NO_TRANSITION

    def on_event(self, robot, event) -> None:
        if isinstance(event, TaskReceivedEvent):

            try:
                robot.task_manager.assign_task(event.task)
            except TaskAlreadyAssignedError:
                robot.comm.publish_task_status(
                    event.task.id,
                    TaskStatus.REJECTED,
                    reason="Robot already has active task"
                )
                return

            robot.comm.request_aisle(
                robot_id=robot.comm.robot_id,
                aisle_id=event.task.aisle_id,
                task_id=event.task.id
            )

            robot.comm.publish_task_status(event.task.id, TaskStatus.IN_PROGRESS)