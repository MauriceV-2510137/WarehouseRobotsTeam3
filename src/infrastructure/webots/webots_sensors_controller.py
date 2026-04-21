from src.interfaces.sensors_controller import SensorsController

class WebotsSensorsController(SensorsController):
    def __init__(self, hardware):
        self.hardware = hardware

    # -------------------
    # Raw scan
    # -------------------
    def get_scan(self):
        return self.hardware.get_lidar_scan()

    # -------------------
    # Semantic LiDAR
    # -------------------
    def get_front_distance(self):
        scan = self.hardware.get_lidar_scan()
        n = len(scan)
        return min(scan[n // 3 : 2 * n // 3])

    def get_left_distance(self):
        scan = self.hardware.get_lidar_scan()
        n = len(scan)
        return min(scan[: n // 3])

    def get_right_distance(self):
        scan = self.hardware.get_lidar_scan()
        n = len(scan)
        return min(scan[2 * n // 3 :])

    # -------------------
    # Orientation
    # -------------------
    def get_yaw(self):
        return self.hardware.get_yaw()

    # -------------------
    # IMU-like sensors
    # -------------------
    def get_gyro(self):
        return self.hardware.get_gyro()

    def get_accelerometer(self):
        return self.hardware.get_accelerometer()

    # -------------------
    # Odometry
    # -------------------
    def get_wheel_positions(self):
        return self.hardware.get_wheel_positions()