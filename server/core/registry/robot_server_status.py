from enum import Enum, auto

class RobotServerStatus(Enum):
    ONLINE = auto()
    IDLE = auto()
    BUSY = auto()
    OFFLINE = auto()