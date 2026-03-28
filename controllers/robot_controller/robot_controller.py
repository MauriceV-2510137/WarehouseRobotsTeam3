"""
Robot controller — runs as a Webots robot controller.

Each robot instance connects to the central server via WebSocket,
receives task assignments, and drives through a state machine:

    IDLE -> MOVING_TO_ENTRY -> WAITING_FOR_AISLE -> MOVING_TO_SHELF
         -> PICKING -> LEAVING_AISLE -> RETURNING -> IDLE

Fix log (v2):
- _get_pose() now reads the correct GPS/compass axes for the Webots
  world where the floor is the XY plane:
    • GPS: x = gps[0], y = gps[1]  (was incorrectly reading gps[2])
    • Compass: angle = atan2(mag[0], mag[1])  (was using mag[0], mag[2])
  These were the primary cause of the robot spinning and jittering
  because it believed it was always at the wrong heading.
- Navigation uses the new unified Navigator (no separate rotate mode).
- Position broadcasts are throttled but not blocked during navigation.
"""

import sys
import math
import threading

# Webots controller API — only import at runtime (mock-friendly)
try:
    from controller import Robot as WebotsRobot
except ImportError:
    WebotsRobot = None

from comms import ServerComms
from navigation import Navigator, Pose


# ---------------------------------------------------------------------------
# Warehouse layout (must match the Webots world and server config)
# ---------------------------------------------------------------------------

# Home position for each robot (keyed by robot name set in Webots)
HOME_POSITIONS: dict[str, Pose] = {
    "robot0": Pose(x=0.0,  y=-0.5, theta=math.pi / 2),
    "robot1": Pose(x=0.5,  y=-0.5, theta=math.pi / 2),
    "robot2": Pose(x=1.0,  y=-0.5, theta=math.pi / 2),
}

# Shelf positions: (aisle, shelf) -> (x, y) in the world frame
# These match the WoodenBox translations in warehouse.wbt
SHELF_POSITIONS: dict[tuple[int, int], tuple[float, float]] = {
    (0, 0): (-2.0,  1.0),
    (0, 1): (-2.0,  2.0),
    (0, 2): (-2.0,  3.0),
    (1, 0): ( 0.0,  1.0),
    (1, 1): ( 0.0,  2.0),
    (1, 2): ( 0.0,  3.0),
    (2, 0): ( 2.0,  1.0),
    (2, 1): ( 2.0,  2.0),
    (2, 2): ( 2.0,  3.0),
}

# Aisle entry waypoints — robot moves here before requesting aisle access
AISLE_ENTRY: dict[int, tuple[float, float]] = {
    0: (-2.0, 0.5),
    1: ( 0.0, 0.5),
    2: ( 2.0, 0.5),
}

PICKING_DURATION_MS = 3000   # ms the robot "picks" the item


# ---------------------------------------------------------------------------
# State machine states
# ---------------------------------------------------------------------------

class State:
    IDLE              = "idle"
    MOVING_TO_ENTRY   = "moving_to_entry"
    WAITING_FOR_AISLE = "waiting_for_aisle"
    MOVING_TO_SHELF   = "moving_to_shelf"
    PICKING           = "picking"
    LEAVING_AISLE     = "leaving_aisle"
    RETURNING         = "returning"


# ---------------------------------------------------------------------------
# Main controller class
# ---------------------------------------------------------------------------

class WarehouseRobotController:
    """
    Drives a single TurtleBot3 in Webots and synchronises with the
    central server. The state machine runs in the Webots main loop;
    server messages arrive on a background thread via ServerComms.
    """

    def __init__(self, robot: "WebotsRobot", robot_id: str, server_url: str):
        self.robot    = robot
        self.robot_id = robot_id
        self.timestep = int(robot.getBasicTimeStep())

        # ── Hardware setup ──────────────────────────────────────────
        self.left_motor  = robot.getDevice("left wheel motor")
        self.right_motor = robot.getDevice("right wheel motor")
        self.left_motor.setPosition(float("inf"))
        self.right_motor.setPosition(float("inf"))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)

        # GPS (enabled at every timestep so readings are always fresh)
        self.gps = robot.getDevice("robot_gps")
        if self.gps:
            self.gps.enable(self.timestep)
        else:
            print(f"[{robot_id}] WARNING: GPS device not found!")

        # Compass
        self.compass = robot.getDevice("robot_compass")
        if self.compass:
            self.compass.enable(self.timestep)
        else:
            print(f"[{robot_id}] WARNING: Compass device not found!")

        # ── Navigator ───────────────────────────────────────────────
        self.navigator = Navigator(
            left_motor=self.left_motor,
            right_motor=self.right_motor,
            max_speed=6.28,
        )

        # ── Server comms ────────────────────────────────────────────
        self.comms = ServerComms(server_url, robot_id)
        self.comms.on_message = self._on_server_message

        # ── State machine ───────────────────────────────────────────
        self.state        = State.IDLE
        self.current_task = None   # dict with task fields from server
        self.pick_start   = None   # simulation time (s) when picking started
        self._aisle_granted = threading.Event()
        self._aisle_denied  = threading.Event()

    # ------------------------------------------------------------------
    # Server message handler  (called from background thread)
    # ------------------------------------------------------------------

    def _on_server_message(self, event: str, data: dict):
        if event == "assign_task":
            self.current_task = data
            self.state = State.MOVING_TO_ENTRY
            self.comms.send_status("moving_to_shelf")
            print(f"[{self.robot_id}] Task assigned: {data}")

        elif event == "aisle_granted":
            self._aisle_granted.set()

        elif event == "aisle_denied":
            # Server told us the aisle is busy; we stay in WAITING_FOR_AISLE
            self._aisle_denied.set()

        elif event == "retry_aisle":
            # Server says the aisle is now free — try again
            self._aisle_denied.clear()
            self._aisle_granted.clear()
            self.comms.request_aisle(data["aisle"])

    # ------------------------------------------------------------------
    # Pose estimation
    # ------------------------------------------------------------------

    def _get_pose(self) -> Pose:
        """
        Return the current robot pose from GPS + compass.

        Coordinate system: Webots floor is the XY plane.
          GPS values: [x, y, z] where z ≈ 0 (robot height above floor).
          We use x = gps[0], y = gps[1].

          Compass returns the north direction in world frame.
          For a robot on the XY plane the heading (angle from +X axis) is:
            theta = atan2(mag[0], mag[1])
          This gives 0 when facing +X and π/2 when facing +Y.

        Note: if your world uses a different "up" axis (e.g. Y-up) you
        may need to swap gps[1]↔gps[2] and adjust the compass formula.
        The warehouse.wbt uses Z-up (default Webots), so the floor
        is XY and this formula is correct.
        """
        gps_vals = self.gps.getValues()
        x = gps_vals[0]
        y = gps_vals[1]  # NOT gps[2] — the floor is the XY plane

        mag_vals = self.compass.getValues()
        # Compass north vector projected onto XY plane → heading angle
        theta = math.atan2(mag_vals[0], mag_vals[1])

        return Pose(x=x, y=y, theta=theta)

    def _send_position(self):
        pose = self._get_pose()
        self.comms.send_position({
            "x": round(pose.x, 3),
            "y": round(pose.y, 3),
            "theta": round(pose.theta, 4),
        })

    # ------------------------------------------------------------------
    # State machine step — called every Webots timestep
    # ------------------------------------------------------------------

    def step(self):
        pose = self._get_pose()

        if self.state == State.IDLE:
            self.navigator.stop()

        elif self.state == State.MOVING_TO_ENTRY:
            aisle = self.current_task["aisle"]
            ex, ey = AISLE_ENTRY[aisle]
            target = Pose(x=ex, y=ey)
            if self.navigator.drive_to(pose, target):
                # Arrived at aisle entry — request exclusive access
                self.state = State.WAITING_FOR_AISLE
                self.comms.send_status("waiting_for_aisle")
                self._aisle_granted.clear()
                self._aisle_denied.clear()
                self.comms.request_aisle(aisle)
                print(f"[{self.robot_id}] Requesting aisle {aisle}")

        elif self.state == State.WAITING_FOR_AISLE:
            self.navigator.stop()
            if self._aisle_granted.is_set():
                self._aisle_granted.clear()
                self.state = State.MOVING_TO_SHELF
                self.comms.send_status("moving_to_shelf")
                print(f"[{self.robot_id}] Aisle granted, heading to shelf")

        elif self.state == State.MOVING_TO_SHELF:
            aisle = self.current_task["aisle"]
            shelf = self.current_task["shelf"]
            sx, sy = SHELF_POSITIONS[(aisle, shelf)]
            target = Pose(x=sx, y=sy)
            if self.navigator.drive_to(pose, target):
                self.state = State.PICKING
                self.pick_start = self.robot.getTime()
                self.comms.send_status("picking")
                print(f"[{self.robot_id}] Picking '{self.current_task['item_name']}'")

        elif self.state == State.PICKING:
            self.navigator.stop()
            elapsed_ms = (self.robot.getTime() - self.pick_start) * 1000
            if elapsed_ms >= PICKING_DURATION_MS:
                aisle = self.current_task["aisle"]
                self.comms.release_aisle(aisle)
                self.state = State.LEAVING_AISLE
                self.comms.send_status("returning")
                print(f"[{self.robot_id}] Done picking, leaving aisle {aisle}")

        elif self.state == State.LEAVING_AISLE:
            aisle = self.current_task["aisle"]
            ex, ey = AISLE_ENTRY[aisle]
            target = Pose(x=ex, y=ey)
            if self.navigator.drive_to(pose, target):
                self.state = State.RETURNING

        elif self.state == State.RETURNING:
            home = HOME_POSITIONS.get(self.robot_id, Pose(0.0, -0.5))
            if self.navigator.drive_to(pose, home):
                self.state = State.IDLE
                self.current_task = None
                self.comms.send_status("idle")
                self.comms.task_complete()
                print(f"[{self.robot_id}] Task complete, back home")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        self.comms.connect()
        print(f"[{self.robot_id}] Connected to server, entering main loop")

        pos_update_interval = 0.5   # seconds between position broadcasts
        last_pos_update = 0.0

        while self.robot.step(self.timestep) != -1:
            self.step()
            now = self.robot.getTime()
            if now - last_pos_update >= pos_update_interval:
                self._send_position()
                last_pos_update = now


# ---------------------------------------------------------------------------
# Entry point (Webots calls this file as the controller)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if WebotsRobot is None:
        print("ERROR: Webots controller API not found. Run this inside Webots.")
        sys.exit(1)

    webots_robot = WebotsRobot()
    robot_id = webots_robot.getName()   # set in Webots robot "Name" field

    server_url = "ws://localhost:8000"
    custom = webots_robot.getCustomData()
    if custom:
        server_url = custom.strip()

    controller = WarehouseRobotController(webots_robot, robot_id, server_url)
    controller.run()
