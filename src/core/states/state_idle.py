from interfaces.robot_state import IRobotState
from core.state_machine import NoTransition

class IdleState(IRobotState):

    def on_enter(self, robot) -> None:
        print("Robot entered Idle state!")
        robot.motion.stop()

    def update(self, robot) -> IRobotState:
        return NoTransition()
    
    