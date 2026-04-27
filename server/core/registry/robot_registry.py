from __future__ import annotations

from typing import Dict, List, Optional

from core.registry.robot_record import RobotRecord
from core.registry.robot_server_status import RobotServerStatus

class RobotRegistry:
    
    def __init__(self) -> None:
        self._robots: Dict[str, RobotRecord] = {}

    def add(self, record: RobotRecord) -> None:
        self._robots[record.robot_id] = record

    def get(self, robot_id: str) -> Optional[RobotRecord]:
        return self._robots.get(robot_id)

    def get_all(self) -> List[RobotRecord]:
        return list(self._robots.values())

    def contains(self, robot_id: str) -> bool:
        return robot_id in self._robots

    def get_by_status(self, status: RobotServerStatus) -> List[RobotRecord]:
        return [r for r in self._robots.values() if r.status == status]

    def get_available(self) -> List[RobotRecord]:
        return [r for r in self._robots.values() if r.is_available()]