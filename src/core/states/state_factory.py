
class StateFactory:

    @staticmethod
    def Idle():
        from core.states.state_idle import IdleState
        return IdleState()

    @staticmethod
    def MoveToShelf():
        from core.states.state_move_to_shelf import MovingToShelfState
        return MovingToShelfState()

    @staticmethod
    def PickItem():
        from core.states.state_pickup_item import PickingItemState
        return PickingItemState()

    @staticmethod
    def MoveToBase():
        from core.states.state_move_to_base import MovingToBaseState
        return MovingToBaseState()