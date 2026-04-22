from interfaces.robot_state import IRobotState
from core.state_machine import NoTransition

class MovingToShelfState(IRobotState):
        
    def on_enter(self, robot) -> None:
        print(f"Robot starting journey to shelf.")

    def update(self, robot) -> IRobotState:
        return NoTransition()