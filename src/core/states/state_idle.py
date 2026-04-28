from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import TaskReceivedEvent
from core.task import TaskStatus, TaskAlreadyAssignedError

class IdleState(IRobotState):

    def on_enter(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        if robot.task_manager.has_task():
            return TransitionID.MOVE_TO_AISLE

        return TransitionID.NO_TRANSITION
    
    def on_event(self, robot, event) -> None:
        if isinstance(event, TaskReceivedEvent):
            try:
                robot.task_manager.assign_task(event.task)
            except TaskAlreadyAssignedError:
                robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")
                return
            except Exception as e:
                robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason=str(e))
                return
            robot.comm.publish_task_status(event.task.id, TaskStatus.PENDING)