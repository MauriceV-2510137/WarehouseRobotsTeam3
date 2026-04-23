from interfaces.robot_state import IRobotState
from core.state_machine import NoTransition

class MovingToShelfState(IRobotState):
    def __init__(self, aisle_id=0):
        self.aisle_id = aisle_id
        self.aisle_granted = False
        
    def on_enter(self, robot):
        print(f"Robot starting journey to shelf in aisle {self.aisle_id}.")
        self.aisle_granted = robot.aisle_manager.request_aisle(self.aisle_id, robot.robot_id)
        if not self.aisle_granted:
            print("Aisle busy, waiting")

    def update(self, robot) -> IRobotState:
        if not self.aisle_granted:
            return NoTransition()
        
        # Debug output
        print(f"Pose: x={robot.pose.x:.2f}, y={robot.pose.y:.2f}, theta={robot.pose.theta:.2f}")
        
        # Compute movement using navigator
        linear, angular = robot.navigator.compute(robot.pose)
        print(f"Computed: linear={linear:.2f}, angular={angular:.2f}")
        
        # Apply movement to motors
        robot.motion.set_wheel_velocities(linear, angular)
        
        # Check if target reached
        if robot.navigator.is_done():
            robot.aisle_manager.release_aisle(self.aisle_id)
            robot.motion.stop()
            from core.states.state_idle import IdleState
            return IdleState()
        
        return NoTransition()
