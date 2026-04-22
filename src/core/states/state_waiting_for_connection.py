from interfaces.robot_state import IRobotState
from core.states.state_idle import IdleState

class WaitingForConnectionState(IRobotState):

    def on_enter(self, robot):
        robot.comm.connect()
        print("Waiting for MQTT connection...")
        robot.motion.stop()

    def update(self, robot) -> IRobotState:
        if robot.comm.is_connected():
            print("MQTT connected!")
            return IdleState()

        return self