from interfaces.robot_state import IRobotState
from core.states.state_machine import NoTransition

from core.states.state_factory import StateFactory

class WaitingForConnectionState(IRobotState):

    def on_enter(self, robot) -> None:
        robot.comm.connect()
        robot.motion.stop()

    def update(self, robot, dt: float) -> IRobotState:
        if robot.comm.is_connected():
            return StateFactory.Idle()

        return NoTransition()