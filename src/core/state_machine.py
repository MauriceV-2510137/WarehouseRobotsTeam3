from interfaces.robot_state import IRobotState

class StateMachine:
    def __init__(self, robot, initial_state: IRobotState):
        self._robot = robot
        self._state = initial_state
        self._state.on_enter(robot)

    def _switch_state(self, state_switch):
        self._state.on_exit(self._robot)
        self._state = state_switch
        self._state.on_enter(self._robot)

    def update(self):
        next_state = self._state.update(self._robot)

        if next_state is not self._state and next_state is not None:
            self._switch_state(next_state)

    def force_state(self, state: IRobotState):
        if state is not None:
            self._switch_state(state)

    def get_state(self):
        return self._state