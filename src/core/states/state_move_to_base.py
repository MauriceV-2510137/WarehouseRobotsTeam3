
from interfaces.robot_state import IRobotState
from core.states.state_machine import NoTransition

from core.states.state_factory import StateFactory

class MovingToBaseState(IRobotState):

    def on_enter(self, robot) -> None:
        print("Returning to base")

        task = robot.task_manager.get_task()
        if not task:
            return

        robot.navigator.set_target(task.base_x, task.base_y)

    def on_exit(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot) -> IRobotState:
        linear, angular = robot.navigator.compute(robot.pose)

        robot.motion.move(linear, angular)

        if robot.navigator.is_done():
            robot.task_manager.complete_task()
            return StateFactory.Idle()

        return NoTransition()