from interfaces.robot_state import IRobotState
from core.states.state_machine import NoTransition

from core.states.state_factory import StateFactory

class IdleState(IRobotState):

    def on_enter(self, robot) -> None:
        print("Robot entered Idle state!")
        robot.motion.stop()

    def update(self, robot, dt: float) -> IRobotState:
        if robot.task_manager.has_task():
            return StateFactory.MoveToShelf()
        return NoTransition()