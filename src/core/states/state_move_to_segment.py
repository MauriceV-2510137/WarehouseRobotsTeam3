from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.task import TaskStatus
from core.events import TaskReceivedEvent

class MovingToSegmentState(IRobotState):

    def on_enter(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return

        print(f"Moving to shelf: {task.segment_pos}")
        robot.navigator.set_target(*task.segment_pos)

    def on_exit(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        linear, angular = robot.navigator.compute(robot.pose)
        robot.motion.move(linear, angular)
        
        if robot.navigator.reached_target():
            robot.navigator.clear_reached()
            return TransitionID.PICK_ITEM

        return TransitionID.NO_TRANSITION
    
    def on_event(self, robot, event) -> None:
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")