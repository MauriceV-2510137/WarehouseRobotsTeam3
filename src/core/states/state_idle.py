from interfaces.robot_state import IRobotState
from core.state_machine import NoTransition

from core.states.state_move_to_shelf import MovingToShelfState

class IdleState(IRobotState):

    def on_enter(self, robot) -> None:
        print("Robot entered Idle state!")
        robot.motion.stop()

    def update(self, robot) -> IRobotState:
        if robot.task_manager.has_task():
            return MovingToShelfState()
        return NoTransition()