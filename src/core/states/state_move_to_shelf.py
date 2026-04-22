from interfaces.robot_state import IRobotState

class MovingToShelfState(IRobotState):
    def __init__(self):
        # This state manages its own sub-states
        pass
        
    def on_enter(self, robot):
        print(f"Robot starting journey to shelf.")
        # Trigger pathfinding here

    def update(self, robot) -> IRobotState:
        return self