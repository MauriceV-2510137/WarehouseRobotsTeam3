from dataclasses import dataclass, field
from typing import Dict, Optional
import time
from core.pose import Pose


@dataclass
class RobotInfo:
    """Information about a registered robot."""
    robot_id: str
    pose: Optional[Pose] = None
    current_task_id: Optional[str] = None
    current_aisle_id: Optional[str] = None
    status: str = "DISCONNECTED"  # DISCONNECTED, IDLE, BUSY
    last_heartbeat: float = 0.0
    registered_at: float = field(default_factory=time.time)


class RobotRegistry:
    """
    Manages registration and tracking of all robots in the warehouse.

    Responsibilities:
    - Register/unregister robots
    - Track robot status (connected, idle, busy)
    - Track robot pose from heartbeats
    - Monitor robot health (detect disconnected robots)
    """

    # Heartbeat timeout in seconds
    HEARTBEAT_TIMEOUT = 30

    def __init__(self):
        self._robots: Dict[str, RobotInfo] = {}

    def register_robot(self, robot_id: str) -> bool:
        """
        Register a new robot.

        Args:
            robot_id: The ID of the robot to register

        Returns:
            True if registered, False if already exists
        """
        if robot_id in self._robots:
            return False

        self._robots[robot_id] = RobotInfo(robot_id=robot_id)
        print(f"[RobotRegistry] Registered robot: {robot_id}")
        return True

    def unregister_robot(self, robot_id: str) -> bool:
        """
        Unregister a robot.

        Args:
            robot_id: The ID of the robot to unregister

        Returns:
            True if unregistered, False if not found
        """
        if robot_id not in self._robots:
            return False

        del self._robots[robot_id]
        print(f"[RobotRegistry] Unregistered robot: {robot_id}")
        return True

    def update_heartbeat(self, robot_id: str, pose: Pose, task_id: Optional[str] = None) -> bool:
        """
        Update robot heartbeat with current pose and task.

        Args:
            robot_id: The ID of the robot
            pose: Current pose of the robot
            task_id: Optional current task ID

        Returns:
            True if updated, False if robot not registered
        """
        current_time = time.time()

        if robot_id not in self._robots:
            # Auto-register new robots
            self.register_robot(robot_id)

        robot = self._robots[robot_id]
        robot.pose = pose
        robot.last_heartbeat = current_time

        if task_id != robot.current_task_id:
            robot.current_task_id = task_id

        # Update status based on task
        if task_id:
            robot.status = "BUSY"
        else:
            robot.status = "IDLE"

        return True

    def update_task_status(self, robot_id: str, task_id: str, status: str):
        """
        Update the task status for a robot.

        Args:
            robot_id: The ID of the robot
            task_id: The ID of the task
            status: The new task status
        """
        if robot_id not in self._robots:
            self.register_robot(robot_id)

        robot = self._robots[robot_id]

        if status in ["DONE", "REJECTED"]:
            # Task finished
            robot.current_task_id = None
            robot.current_aisle_id = None
            robot.status = "IDLE"
        else:
            robot.current_task_id = task_id
            robot.status = "BUSY"

    def set_aisle(self, robot_id: str, aisle_id: Optional[str]):
        """Set the current aisle for a robot."""
        if robot_id in self._robots:
            self._robots[robot_id].current_aisle_id = aisle_id

    def get_robot(self, robot_id: str) -> Optional[RobotInfo]:
        """Get robot info by ID."""
        return self._robots.get(robot_id)

    def get_all_robots(self) -> Dict[str, RobotInfo]:
        """Get all registered robots."""
        return self._robots.copy()

    def get_connected_robots(self) -> Dict[str, RobotInfo]:
        """Get all robots with recent heartbeats."""
        current_time = time.time()
        result = {}

        for robot_id, robot in self._robots.items():
            if current_time - robot.last_heartbeat < self.HEARTBEAT_TIMEOUT:
                result[robot_id] = robot

        return result

    def get_disconnected_robots(self) -> Dict[str, RobotInfo]:
        """Get all robots that haven't sent heartbeats recently."""
        current_time = time.time()
        result = {}

        for robot_id, robot in self._robots.items():
            if current_time - robot.last_heartbeat >= self.HEARTBEAT_TIMEOUT:
                result[robot_id] = robot

        return result

    def is_connected(self, robot_id: str) -> bool:
        """Check if a robot is connected (recent heartbeat)."""
        if robot_id not in self._robots:
            return False

        current_time = time.time()
        return (current_time - self._robots[robot_id].last_heartbeat) < self.HEARTBEAT_TIMEOUT

    def get_robot_count(self) -> int:
        """Get total number of registered robots."""
        return len(self._robots)

    def get_connected_count(self) -> int:
        """Get number of connected robots."""
        return len(self.get_connected_robots())

    def get_idle_robots(self) -> Dict[str, RobotInfo]:
        """Get all idle robots."""
        return {
            robot_id: robot
            for robot_id, robot in self._robots.items()
            if robot.status == "IDLE" and self.is_connected(robot_id)
        }

    def get_busy_robots(self) -> Dict[str, RobotInfo]:
        """Get all busy robots."""
        return {
            robot_id: robot
            for robot_id, robot in self._robots.items()
            if robot.status == "BUSY"
        }

    def cleanup_disconnected(self) -> int:
        """
        Remove robots that have been disconnected for too long.

        Returns:
            Number of robots removed
        """
        disconnected = self.get_disconnected_robots()
        for robot_id in disconnected:
            self.unregister_robot(robot_id)

        return len(disconnected)

    def get_status_summary(self) -> str:
        """Get a summary of all robot statuses."""
        lines = ["=== Robot Registry Summary ==="]
        lines.append(f"Total registered: {self.get_robot_count()}")
        lines.append(f"Connected: {self.get_connected_count()}")
        lines.append(f"Idle: {len(self.get_idle_robots())}")
        lines.append(f"Busy: {len(self.get_busy_robots())}")
        lines.append("")

        for robot_id, robot in self._robots.items():
            connected = "✓" if self.is_connected(robot_id) else "✗"
            lines.append(f"Robot {robot_id} [{connected}]: {robot.status}")
            if robot.pose:
                lines.append(f"  Pose: ({robot.pose.x:.2f}, {robot.pose.y:.2f}, {robot.pose.theta:.2f})")
            if robot.current_task_id:
                lines.append(f"  Task: {robot.current_task_id}")
            if robot.current_aisle_id:
                lines.append(f"  Aisle: {robot.current_aisle_id}")

        return "\n".join(lines)
