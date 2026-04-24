import math

class WebotsHardware:
    def __init__(self, robot, model):
        self.robot = robot
        self.model = model

        self.timestep = int(robot.getBasicTimeStep())

        # -------------------
        # Actuators (motors)
        # -------------------
        self.left_motor = robot.getDevice("left wheel motor")
        self.right_motor = robot.getDevice("right wheel motor")

        self.left_motor.setPosition(float("inf"))
        self.right_motor.setPosition(float("inf"))

        # -------------------
        # Sensors
        # -------------------
        # LiDAR
        self.lidar = robot.getDevice("LDS-01")
        self.lidar.enable(self.timestep)

        # Compass (used for yaw)
        self.compass = robot.getDevice("compass")
        self.compass.enable(self.timestep)

        # Gyro
        self.gyro = robot.getDevice("gyro")
        self.gyro.enable(self.timestep)

        # Accelerometer
        self.accelerometer = robot.getDevice("accelerometer")
        self.accelerometer.enable(self.timestep)

        # Wheel encoders
        self.left_encoder = self.left_motor.getPositionSensor()
        self.right_encoder = self.right_motor.getPositionSensor()
        self.left_encoder.enable(self.timestep)
        self.right_encoder.enable(self.timestep)

    # -------------------
    # Timing
    # -------------------
    def get_time_step(self):
        return self.timestep

    # -------------------
    # Actuators
    # -------------------
    def set_wheel_velocity(self, left: float, right: float):
        self.left_motor.setVelocity(left)
        self.right_motor.setVelocity(right)

    # -------------------
    # LiDAR
    # -------------------
    def get_lidar_scan(self):
        return self.lidar.getRangeImage()

    def get_lidar_meta(self):
        return {
            "fov": self.lidar.getFov(),
            "horizontal_resolution": self.lidar.getHorizontalResolution(),
            "range_min": self.lidar.getMinRange(),
            "range_max": self.lidar.getMaxRange(),
        }

    # -------------------
    # Orientation (yaw only)
    # -------------------
    def get_yaw(self):
        north = self.compass.getValues()
        return math.atan2(north[0], north[2])

    # -------------------
    # IMU-like sensors
    # -------------------
    def get_gyro(self):
        return self.gyro.getValues()

    def get_accelerometer(self):
        return self.accelerometer.getValues()

    # -------------------
    # Odometry
    # -------------------
    def get_wheel_positions(self):
        return (
            self.left_encoder.getValue(),
            self.right_encoder.getValue(),
        )