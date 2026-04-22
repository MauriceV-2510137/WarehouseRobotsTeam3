from interfaces.robot_state import IRobotState
from core.state_machine import NoTransition
from core.states.state_idle import IdleState

class WaitingForConnectionState(IRobotState):

    def on_enter(self, robot) -> None:
        robot.comm.connect()
        print("Waiting for MQTT connection...")
        robot.motion.stop()

    def update(self, robot) -> IRobotState:
        if robot.comm.is_connected():
            print("MQTT connected!")
            return IdleState()

        return NoTransition()