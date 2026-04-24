from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import Event

from core.states.state_idle import IdleState
from core.states.state_move_to_aisle_entry import MovingToAisleEntryState
from core.states.state_move_to_segment import MovingToSegmentState
from core.states.state_pickup_item import PickingItemState
from core.states.state_move_to_base import MovingToBaseState
from core.states.state_waiting_for_connection import WaitingForConnectionState
from core.states.state_wait_for_aisle_access import WaitingForAisleState

class StateMachine:
    def __init__(self, robot, initial_state: TransitionID):
        self._robot = robot
        self._registry = self._build_registry()
        self._state = self._create(initial_state)
        self._state.on_enter(robot)

    def _build_registry(self):
        return {
            TransitionID.WAIT_CONNECTION: WaitingForConnectionState,
            TransitionID.IDLE: IdleState,
            TransitionID.MOVE_TO_AISLE: MovingToAisleEntryState,
            TransitionID.WAIT_FOR_AISLE_ACCESS: WaitingForAisleState,
            TransitionID.MOVE_TO_SEGMENT: MovingToSegmentState,
            TransitionID.PICK_ITEM: PickingItemState,
            TransitionID.MOVE_TO_BASE: MovingToBaseState,
        }
    
    def _create(self, state_id: TransitionID) -> IRobotState:
        state_cls = self._registry.get(state_id, IdleState)
        return state_cls()

    def _switch(self, next_state_id: TransitionID):
        self._state.on_exit(self._robot)
        self._state = self._create(next_state_id)
        self._state.on_enter(self._robot)

    def update(self, dt: float):
        result = self._state.update(self._robot, dt)
        if result == TransitionID.NO_TRANSITION:
            return
        self._switch(result)

    def handle_event(self, event: Event):
        self._state.on_event(self._robot, event)

    def force_state(self, state_id: TransitionID):
        self._switch(state_id)

    def get_state(self):
        return self._state