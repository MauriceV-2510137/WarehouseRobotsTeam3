from interfaces.robot_state import IRobotState

class IdleState(IRobotState):

    def update(self, robot) -> IRobotState:
        return self
    
    def on_enter(self, robot):
        print("Robot entered Idle state!")
        robot.motion.stop()