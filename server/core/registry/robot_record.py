from dataclasses import dataclass, field
from datetime import datetime

from server.core.time_utils import get_now

from core.pose import Pose
from server.core.registry.robot_server_status import RobotServerStatus

@dataclass
class RobotRecord:
    robot_id: str
    status: RobotServerStatus = RobotServerStatus.ONLINE
    pose: Pose = field(default_factory=Pose)
    active_task_id: str | None = None
    last_heartbeat: datetime = field(default_factory=get_now)
    registered_at: datetime = field(default_factory=get_now)

    def is_available(self) -> bool:
        return self.status == RobotServerStatus.IDLE