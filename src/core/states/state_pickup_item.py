import random

from interfaces.robot_state import IRobotState
from core.states.state_machine import NoTransition

from core.states.state_factory import StateFactory

class PickingItemState(IRobotState):

    def __init__(self):
        self.wait_duration = 0.0
        self.current_wait_time = 0.0

    def on_enter(self, robot) -> None:
        self.wait_duration = random.uniform(5, 10)
        robot.motion.stop()
        print("Picking up item...")

    def on_exit(self, robot):
        self.current_wait_time = 0.0

    def update(self, robot, dt: float) -> IRobotState:

        self.current_wait_time += dt

        if self.current_wait_time >= self.wait_duration:
            return StateFactory.MoveToBase()

        return NoTransition()