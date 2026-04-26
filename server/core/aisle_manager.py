from dataclasses import dataclass, field
from typing import Dict, Optional
import time


@dataclass
class AisleLock:
    """Represents a lock on an aisle."""
    aisle_id: str
    robot_id: str
    task_id: str
    acquired_at: float
    expires_at: float


class AisleManager:
    """
    Manages aisle locking for the warehouse system.

    Responsibilities:
    - Track which aisles are locked and by which robot
    - Grant or deny aisle access requests
    - Release locks when robots disconnect or timeout
    - Handle lock expiration
    """

    DEFAULT_LOCK_TIMEOUT = 300  # 5 minutes

    def __init__(self, lock_timeout: float = DEFAULT_LOCK_TIMEOUT):
        self._locks: Dict[str, AisleLock] = {}
        self._robot_aisles: Dict[str, str] = {}
        self._lock_timeout = lock_timeout

    def request_aisle(self, robot_id: str, aisle_id: str, task_id: str) -> bool:
        current_time = time.time()

        if aisle_id in self._locks:
            lock = self._locks[aisle_id]
            if current_time > lock.expires_at:
                self._release_lock(aisle_id)
            elif lock.robot_id == robot_id:
                self._extend_lock(aisle_id, task_id)
                return True
            else:
                return False

        self._acquire_lock(robot_id, aisle_id, task_id, current_time)
        return True

    def release_aisle(self, robot_id: str, aisle_id: Optional[str] = None) -> bool:
        if aisle_id is not None:
            if aisle_id in self._locks and self._locks[aisle_id].robot_id == robot_id:
                self._release_lock(aisle_id)
                return True
            return False
        else:
            to_release = [aid for aid, lock in self._locks.items() if lock.robot_id == robot_id]
            for aid in to_release:
                self._release_lock(aid)
            return len(to_release) > 0

    def release_robot(self, robot_id: str) -> int:
        aisles_to_release = [aid for aid, lock in self._locks.items() if lock.robot_id == robot_id]
        for aid in aisles_to_release:
            self._release_lock(aid)
        return len(aisles_to_release)

    def is_aisle_locked(self, aisle_id: str) -> bool:
        if aisle_id not in self._locks:
            return False
        if time.time() > self._locks[aisle_id].expires_at:
            self._release_lock(aisle_id)
            return False
        return True

    def get_locked_aisles(self) -> Dict[str, str]:
        current_time = time.time()
        result = {}
        for aisle_id, lock in list(self._locks.items()):
            if current_time > lock.expires_at:
                self._release_lock(aisle_id)
            else:
                result[aisle_id] = lock.robot_id
        return result

    def get_robot_aisle(self, robot_id: str) -> Optional[str]:
        return self._robot_aisles.get(robot_id)

    def cleanup_expired_locks(self) -> int:
        current_time = time.time()
        expired = [aid for aid, lock in self._locks.items() if current_time > lock.expires_at]
        for aid in expired:
            self._release_lock(aid)
        return len(expired)

    def _acquire_lock(self, robot_id: str, aisle_id: str, task_id: str, current_time: float):
        self._locks[aisle_id] = AisleLock(
            aisle_id=aisle_id,
            robot_id=robot_id,
            task_id=task_id,
            acquired_at=current_time,
            expires_at=current_time + self._lock_timeout
        )
        self._robot_aisles[robot_id] = aisle_id
        print(f"[AisleManager] Robot {robot_id} locked aisle {aisle_id} (expires in {self._lock_timeout}s)")

    def _extend_lock(self, aisle_id: str, task_id: str):
        lock = self._locks[aisle_id]
        lock.expires_at = time.time() + self._lock_timeout
        lock.task_id = task_id
        print(f"[AisleManager] Extended lock for aisle {aisle_id}")

    def _release_lock(self, aisle_id: str):
        if aisle_id in self._locks:
            robot_id = self._locks[aisle_id].robot_id
            del self._locks[aisle_id]
            if robot_id in self._robot_aisles:
                del self._robot_aisles[robot_id]
            print(f"[AisleManager] Released lock on aisle {aisle_id} (was held by {robot_id})")
