import math


class WebotsHardware:
    """
    Low-level Webots hardware abstraction for the TurtleBot3 Burger.

    Coordinate frame (Webots R2025a, Z-up):
        X = forward  (robot's nose points in +X direction)
        Y = left     (positive Y = left of robot)
        Z = up       (positive Z = upward)

    Device names confirmed for TurtleBot3Burger.proto:
        Motors        : "left wheel motor" / "right wheel motor"
        LiDAR         : "LDS-01"
        Compass       : "compass"
        Gyro          : "gyro"
        Accelerometer : "accelerometer"
        Encoders      : position sensor embedded in each motor (no separate name)
    """

    def __init__(self, robot, model) -> None:
        self.robot = robot
        self.model = model
        self.timestep = int(robot.getBasicTimeStep())

        # ---------------------------------------------------------------
        # Actuators
        # ---------------------------------------------------------------
        self.left_motor  = robot.getDevice("left wheel motor")
        self.right_motor = robot.getDevice("right wheel motor")

        # Velocity-control mode: set position to infinity, then drive by velocity.
        self.left_motor.setPosition(float("inf"))
        self.right_motor.setPosition(float("inf"))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)

        # ---------------------------------------------------------------
        # LiDAR  (2-D range scanner, 360 degrees)
        # ---------------------------------------------------------------
        self.lidar = robot.getDevice("LDS-01")
        self.lidar.enable(self.timestep)

        # ---------------------------------------------------------------
        # Compass
        # ---------------------------------------------------------------
        self.compass = robot.getDevice("compass")
        self.compass.enable(self.timestep)

        # ---------------------------------------------------------------
        # IMU sensors
        # ---------------------------------------------------------------
        self.gyro = robot.getDevice("gyro")
        self.gyro.enable(self.timestep)

        self.accelerometer = robot.getDevice("accelerometer")
        self.accelerometer.enable(self.timestep)

        # ---------------------------------------------------------------
        # Wheel encoders  (position sensor embedded in each motor)
        # ---------------------------------------------------------------
        self.left_encoder  = self.left_motor.getPositionSensor()
        self.right_encoder = self.right_motor.getPositionSensor()
        self.left_encoder.enable(self.timestep)
        self.right_encoder.enable(self.timestep)

    # -------------------------------------------------------------------
    # Timing
    # -------------------------------------------------------------------
    def get_time_step(self) -> int:
        return self.timestep

    # -------------------------------------------------------------------
    # Actuators
    # -------------------------------------------------------------------
    def set_wheel_velocity(self, left: float, right: float) -> None:
        self.left_motor.setVelocity(left)
        self.right_motor.setVelocity(right)

    # -------------------------------------------------------------------
    # LiDAR
    # -------------------------------------------------------------------
    def get_lidar_scan(self) -> list:
        return self.lidar.getRangeImage()

    def get_lidar_meta(self) -> dict:
        return {
            "fov":                   self.lidar.getFov(),
            "horizontal_resolution": self.lidar.getHorizontalResolution(),
            "range_min":             self.lidar.getMinRange(),
            "range_max":             self.lidar.getMaxRange(),
        }

    # -------------------------------------------------------------------
    # Orientation  (compass)
    # -------------------------------------------------------------------
    def get_yaw(self) -> float:
        north = self.compass.getValues()
        return math.atan2(north[0], north[1])

    # -------------------------------------------------------------------
    # IMU sensors
    # -------------------------------------------------------------------
    def get_gyro(self) -> list:
        return self.gyro.getValues()

    def get_accelerometer(self) -> list:
        return self.accelerometer.getValues()

    # -------------------------------------------------------------------
    # Wheel encoders
    # -------------------------------------------------------------------
    def get_wheel_positions(self) -> tuple:
        return (
            self.left_encoder.getValue(),
            self.right_encoder.getValue(),
        )