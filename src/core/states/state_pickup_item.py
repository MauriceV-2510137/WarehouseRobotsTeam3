import random

from interfaces.robot_state import IRobotState
from core.states.state_machine import NoTransition

from core.states.state_factory import StateFactory

class PickingItemState(IRobotState):

    def on_enter(self, robot) -> None:
        print("Picking item...")
        self.start_time = robot.sim_time
        self.duration = random.uniform(5, 10)
        robot.motion.stop()

    def update(self, robot) -> IRobotState:
        if robot.sim_time - self.start_time >= self.duration:
            return StateFactory.MoveToBase()

        return NoTransition()