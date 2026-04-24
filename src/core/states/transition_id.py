from enum import Enum, auto

class TransitionID(Enum):
    NO_TRANSITION = auto()

    WAIT_CONNECTION = auto()

    IDLE = auto()
    MOVE_TO_AISLE = auto()
    WAIT_FOR_AISLE_ACCESS = auto()
    MOVE_TO_SEGMENT = auto()
    PICK_ITEM = auto()
    MOVE_TO_BASE = auto()
    