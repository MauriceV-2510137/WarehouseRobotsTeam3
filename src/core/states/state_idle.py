from interfaces.robot_state import IRobotState
from core.state_machine import NoTransition

from core.states.state_move_to_shelf import MovingToShelfState

class IdleState(IRobotState):

    def update(self, robot) -> IRobotState:
        # Check if there are tasks in the queue
        task = robot.task_manager.get_next_task()
        if task:
            if task.task_type == 'move_to_shelf':
                robot.navigator.set_target(task.params['x'], task.params['y'])
                return MovingToShelfState(task.params.get('aisle', 0))
        return NoTransition()
    
    def on_enter(self, robot):
        print("Robot entered Idle state!")
        robot.motion.stop()