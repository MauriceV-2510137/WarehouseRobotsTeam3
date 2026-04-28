from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.task import TaskStatus
from core.events import TaskReceivedEvent

class MovingToBaseState(IRobotState):

    def on_enter(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return

        robot.reset_collision_state()
        hx, hy = robot.home

        # Approach home from the east to avoid the column of idle robots at x≈0.
        # Go to (1.5, hy) first, then west to home.
        self._waypoints = [(1.5, hy), (hx, hy)]
        target = self._waypoints.pop(0)
        print(f"Returning to base from ({robot.pose.x:.2f},{robot.pose.y:.2f}) via {target} -> {robot.home}")
        robot.navigator.set_target(*target)

    def on_exit(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        linear, angular = robot.navigator.compute(robot.pose)
        robot.safe_move(linear, angular, dt)

        if robot.navigator.reached_target():
            robot.navigator.clear_reached()
            if self._waypoints:
                robot.reset_collision_state()
                robot.navigator.set_target(*self._waypoints.pop(0))
                return TransitionID.NO_TRANSITION
            task = robot.task_manager.get_task()
            if task:
                robot.comm.publish_task_status(task.id, TaskStatus.DONE)
                robot.task_manager.complete_task()
            return TransitionID.IDLE

        return TransitionID.NO_TRANSITION

    def on_event(self, robot, event):
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")
