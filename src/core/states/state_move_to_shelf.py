from interfaces.robot_state import IRobotState
from core.states.state_machine import NoTransition

from core.states.state_factory import StateFactory

class MovingToShelfState(IRobotState):
        
    def on_enter(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return
        
        print("Moving to shelf:")
        
        robot.task_manager.start_task()
        robot.navigator.set_target(task.shelf_x, task.shelf_y)

    def on_exit(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> IRobotState:
        linear, angular = robot.navigator.compute(robot.pose)

        robot.motion.move(linear, angular)

        # arrived
        if robot.navigator.is_done():
            return StateFactory.PickItem()
        
        return NoTransition()