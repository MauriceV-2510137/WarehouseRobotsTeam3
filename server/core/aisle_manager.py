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
    
    # Lock timeout in seconds (configurable)
    DEFAULT_LOCK_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, lock_timeout: float = DEFAULT_LOCK_TIMEOUT):
        self._locks: Dict[str, AisleLock] = {}  # aisle_id -> AisleLock
        self._robot_aisles: Dict[str, str] = {}  # robot_id -> aisle_id (reverse lookup)
        self._lock_timeout = lock_timeout
    
    def request_aisle(self, robot_id: str, aisle_id: str, task_id: str) -> bool:
        """
        Request access to an aisle.
        
        Args:
            robot_id: The ID of the robot requesting access
            aisle_id: The ID of the aisle to access
            task_id: The ID of the task requiring aisle access
            
        Returns:
            True if access is granted, False if denied
        """
        current_time = time.time()
        
        # Check if aisle is already locked
        if aisle_id in self._locks:
            lock = self._locks[aisle_id]
            
            # Check if lock has expired
            if current_time > lock.expires_at:
                # Lock expired, release it
                self._release_lock(aisle_id)
            elif lock.robot_id == robot_id:
                # Same robot already has lock, grant access
                # Extend the lock
                self._extend_lock(aisle_id, task_id)
                return True
            else:
                # Different robot has lock, deny access
                return False
        
        # Grant new lock
        self._acquire_lock(robot_id, aisle_id, task_id, current_time)
        return True
    
    def release_aisle(self, robot_id: str, aisle_id: Optional[str] = None) -> bool:
        """
        Release an aisle lock.
        
        Args:
            robot_id: The ID of the robot releasing the lock
            aisle_id: The specific aisle to release, or None to release all for robot
            
        Returns:
            True if release was successful, False if no lock was held
        """
        if aisle_id is not None:
            # Release specific aisle
            if aisle_id in self._locks and self._locks[aisle_id].robot_id == robot_id:
                self._release_lock(aisle_id)
                return True
            return False
        else:
            # Release all aisles for robot
            released = False
            to_release = [
                aid for aid, lock in self._locks.items() 
                if lock.robot_id == robot_id
            ]
            for aid in to_release:
                self._release_lock(aid)
                released = True
            return released
    
    def release_robot(self, robot_id: str) -> int:
        """
        Release all locks held by a robot (e.g., when robot disconnects).
        
        Args:
            robot_id: The ID of the robot
            
        Returns:
            Number of locks released
        """
        aisles_to_release = [
            aid for aid, lock in self._locks.items()
            if lock.robot_id == robot_id
        ]
        for aid in aisles_to_release:
            self._release_lock(aid)
        return len(aisles_to_release)
    
    def is_aisle_locked(self, aisle_id: str) -> bool:
        """Check if an aisle is currently locked."""
        if aisle_id not in self._locks:
            return False
        
        # Check for expiration
        if time.time() > self._locks[aisle_id].expires_at:
            self._release_lock(aisle_id)
            return False
        
        return True
    
    def get_locked_aisles(self) -> Dict[str, str]:
        """
        Get all currently locked aisles.
        
        Returns:
            Dictionary mapping aisle_id to robot_id
        """
        current_time = time.time()
        result = {}
        
        for aisle_id, lock in list(self._locks.items()):
            if current_time > lock.expires_at:
                self._release_lock(aisle_id)
            else:
                result[aisle_id] = lock.robot_id
        
        return result
    
    def get_robot_aisle(self, robot_id: str) -> Optional[str]:
        """Get the aisle currently locked by a robot, if any."""
        return self._robot_aisles.get(robot_id)
    
    def cleanup_expired_locks(self) -> int:
        """
        Clean up all expired locks.
        
        Returns:
            Number of locks cleaned up
        """
        current_time = time.time()
        expired = [
            aisle_id for aisle_id, lock in self._locks.items()
            if current_time > lock.expires_at
        ]
        
        for aisle_id in expired:
            self._release_lock(aisle_id)
        
        return len(expired)
    
    def _acquire_lock(self, robot_id: str, aisle_id: str, task_id: str, current_time: float):
        """Acquire a new lock on an aisle."""
        expires_at = current_time + self._lock_timeout
        
        self._locks[aisle_id] = AisleLock(
            aisle_id=aisle_id,
            robot_id=robot_id,
            task_id=task_id,
            acquired_at=current_time,
            expires_at=expires_at
        )
        
        self._robot_aisles[robot_id] = aisle_id
        print(f"[AisleManager] Robot {robot_id} locked aisle {aisle_id} (expires in {self._lock_timeout}s)")
    
    def _extend_lock(self, aisle_id: str, task_id: str):
        """Extend the lock timeout for an existing lock."""
        lock = self._locks[aisle_id]
        current_time = time.time()
        lock.expires_at = current_time + self._lock_timeout
        lock.task_id = task_id  # Update task_id in case it changed
        print(f"[AisleManager] Extended lock for aisle {aisle_id}")
    
    def _release_lock(self, aisle_id: str):
        """Release a lock on an aisle."""
        if aisle_id in self._locks:
            lock = self._locks[aisle_id]
            robot_id = lock.robot_id
            
            del self._locks[aisle_id]
            
            if robot_id in self._robot_aisles:
                del self._robot_aisles[robot_id]
            
            print(f"[AisleManager] Released lock on aisle {aisle_id} (was held by {robot_id})")