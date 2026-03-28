import sys
import math
from enum import Enum, auto

try:
    from controller import Robot as WebotsRobot
except ImportError:
    WebotsRobot = None

from comms import ServerComms
from navigation import Pose, WheelController
from warehouse_layout import AISLES, ROBOT_HOMES, HOME_DEFAULT

DWELL_DURATION_S = 3.0
POS_BROADCAST_HZ = 2.0
GOAL_TOLERANCE = 0.15  # Increased so Webots physics don't cause infinite circling

class State(Enum):
    IDLE = auto()
    MOVING_TO_ENTRY = auto()
    WAITING_AISLE = auto()
    MOVING_TO_TARGET = auto()
    DWELLING = auto()
    RETURNING = auto()

class RobotController:
    def __init__(self, robot: "WebotsRobot", robot_id: str, server_url: str):
        self._robot = robot
        self._id = robot_id
        self._ts = int(robot.getBasicTimeStep())
        
        self._setup_hardware()
        self._wheels = WheelController(self._left_motor, self._right_motor, 6.28)
        
        self._comms = ServerComms(server_url, robot_id)
        self._comms.on_message = self._on_server_message

        self._state = State.IDLE
        self._task = None
        self._dwell_until = 0.0
        self._aisle_granted = False

    def _setup_hardware(self):
        self._left_motor = self._robot.getDevice("left wheel motor")
        self._right_motor = self._robot.getDevice("right wheel motor")
        for m in (self._left_motor, self._right_motor):
            m.setPosition(float("inf"))
            m.setVelocity(0.0)

        self._gps = self._robot.getDevice("robot_gps")
        self._compass = self._robot.getDevice("robot_compass")
        for s in (self._gps, self._compass):
            if s: s.enable(self._ts)

    def _pose(self) -> Pose:
        g = self._gps.getValues()
        c = self._compass.getValues()
        return Pose(x=g[0], y=g[1], theta=math.atan2(c[0], c[1]))

    def _on_server_message(self, event: str, data: dict):
        if event == "assign_task":
            self._task = data
            self._state = State.MOVING_TO_ENTRY
            self._comms.send_status("moving")
            print(f"[{self._id}] Assigned aisle {data['aisle']}")
        elif event == "aisle_granted":
            self._aisle_granted = True
        elif event == "retry_aisle":
            if self._state == State.WAITING_AISLE and self._task:
                self._comms.request_aisle(self._task["aisle"])

    def _drive_to(self, pose: Pose, target_x: float, target_y: float) -> bool:
        dist = pose.distance_to(target_x, target_y)
        if dist < GOAL_TOLERANCE:
            self._wheels.stop()
            return True

        err = pose.heading_error(target_x, target_y)
        angular = max(-6.28, min(6.28, 3.0 * err))
        linear = min(4.0 * dist * max(0.0, math.cos(err)), 6.28)
        
        self._wheels.drive(linear, angular)
        return False

    def _tick(self, now: float, pose: Pose):
        aisle = AISLES.get(self._task["aisle"]) if self._task else None
        home = ROBOT_HOMES.get(self._id, HOME_DEFAULT)

        if self._state == State.IDLE:
            self._wheels.stop()

        elif self._state == State.MOVING_TO_ENTRY:
            if self._drive_to(pose, aisle.entry.x, aisle.entry.y):
                self._state = State.WAITING_AISLE
                self._aisle_granted = False
                self._comms.request_aisle(aisle.index)
                self._comms.send_status("waiting_for_aisle")

        elif self._state == State.WAITING_AISLE:
            self._wheels.stop()
            if self._aisle_granted:
                self._state = State.MOVING_TO_TARGET
                self._comms.send_status("moving")

        elif self._state == State.MOVING_TO_TARGET:
            if self._drive_to(pose, aisle.target.x, aisle.target.y):
                self._state = State.DWELLING
                self._dwell_until = now + DWELL_DURATION_S
                self._comms.send_status("dwelling")

        elif self._state == State.DWELLING:
            self._wheels.stop()
            if now >= self._dwell_until:
                self._comms.release_aisle(aisle.index)
                self._state = State.RETURNING
                self._comms.send_status("returning")

        elif self._state == State.RETURNING:
            if self._drive_to(pose, home.x, home.y):
                self._state = State.IDLE
                self._task = None
                self._comms.send_status("idle")
                self._comms.task_complete()
                print(f"[{self._id}] Task complete, ready for next.")

    def run(self):
        self._comms.connect()
        last_pos_time = 0.0

        while self._robot.step(self._ts) != -1:
            now = self._robot.getTime()
            pose = self._pose()
            self._tick(now, pose)

            if now - last_pos_time >= (1.0 / POS_BROADCAST_HZ):
                self._comms.send_position({"x": pose.x, "y": pose.y, "theta": pose.theta})
                last_pos_time = now

if __name__ == "__main__":
    if WebotsRobot is None: sys.exit(1)
    bot = WebotsRobot()
    RobotController(bot, bot.getName(), bot.getCustomData().strip() or "ws://localhost:8000").run()