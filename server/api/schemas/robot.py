from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

class RobotStatus(str, Enum):
    ONLINE  = "ONLINE"
    IDLE    = "IDLE"
    BUSY    = "BUSY"
    OFFLINE = "OFFLINE"


class PoseSchema(BaseModel):
    x: float
    y: float
    theta: float


class RobotSchema(BaseModel):
    robot_id: str
    status: RobotStatus
    pose: PoseSchema
    active_task_id: Optional[str]
    last_heartbeat: datetime
    registered_at: datetime