from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID

class WaitingForConnectionState(IRobotState):

    def on_enter(self, robot) -> None:
        robot.comm.connect()
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        if robot.comm.is_connected():
            return TransitionID.IDLE

        return TransitionID.NO_TRANSITION