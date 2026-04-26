import math
from interfaces.sensors_controller import ISensorsController


class WebotsSensorsController(ISensorsController):
    """
    Thin abstraction layer over WebotsHardware.
    Keeps the robot core fully independent from the Webots API.
    """

    def __init__(self, hardware):
        self.hardware = hardware
        self._max_range = None   # lazily initialised on first scan

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _get_max_range(self) -> float:
        if self._max_range is None:
            meta = self.hardware.get_lidar_meta()
            self._max_range = meta["range_max"]
        return self._max_range

    def _clean(self, scan: list) -> list:
        """Replace inf/nan values with max_range so min() is always finite."""
        max_r = self._get_max_range()
        return [v if math.isfinite(v) else max_r for v in scan]

    def _sector_min(self, scan: list, center: int, half: int) -> float:
        """
        Return the minimum range value in the sector [center-half, center+half],
        wrapping around if necessary.
        """
        n = len(scan)
        indices = range(center - half, center + half + 1)
        return min(scan[i % n] for i in indices)

    # -------------------------------------------------------------------
    # Raw scan
    # -------------------------------------------------------------------
    def get_scan(self) -> list:
        """Returns the raw 360-degree range image (may contain inf values)."""
        return self.hardware.get_lidar_scan()

    # -------------------------------------------------------------------
    # Semantic distances
    # -------------------------------------------------------------------

    def get_front_distance(self) -> float:
        """
        Minimum range in the forward 30-degree cone (+/-15 deg around +X).
        Index 0 is forward, the sector wraps around the end of the array.
        """
        scan = self._clean(self.hardware.get_lidar_scan())
        n    = len(scan)
        half = max(1, n // 24)       # half of 30-deg sector = 15 deg
        return self._sector_min(scan, center=0, half=half)

    def get_left_distance(self) -> float:
        """
        Minimum range in the left 30-degree cone (+/-15 deg around +Y).
        +Y is 90 deg CCW from +X, which is index n//4.
        """
        scan = self._clean(self.hardware.get_lidar_scan())
        n    = len(scan)
        half = max(1, n // 24)
        return self._sector_min(scan, center=n // 4, half=half)

    def get_right_distance(self) -> float:
        """
        Minimum range in the right 30-degree cone (+/-15 deg around -Y).
        -Y is 270 deg CCW from +X, which is index 3*n//4.
        """
        scan = self._clean(self.hardware.get_lidar_scan())
        n    = len(scan)
        half = max(1, n // 24)
        return self._sector_min(scan, center=3 * n // 4, half=half)

    def get_rear_distance(self) -> float:
        """
        Minimum range in the rear 30-degree cone (+/-15 deg around -X).
        -X is 180 deg CCW from +X, which is index n//2.
        """
        scan = self._clean(self.hardware.get_lidar_scan())
        n    = len(scan)
        half = max(1, n // 24)
        return self._sector_min(scan, center=n // 2, half=half)

    # -------------------------------------------------------------------
    # Orientation
    # -------------------------------------------------------------------

    def get_yaw(self) -> float:
        """
        Returns the compass-based heading in radians.
        0 = forward (+X), +pi/2 = left (+Y), -pi/2 = right (-Y).
        See WebotsHardware.get_yaw() for full derivation.
        """
        return self.hardware.get_yaw()

    # -------------------------------------------------------------------
    # IMU
    # -------------------------------------------------------------------

    def get_gyro(self) -> list:
        """[wx, wy, wz] angular velocity in rad/s (robot local frame)."""
        return self.hardware.get_gyro()

    def get_accelerometer(self) -> list:
        """[ax, ay, az] linear acceleration in m/s2 (robot local frame)."""
        return self.hardware.get_accelerometer()

    # -------------------------------------------------------------------
    # Wheel encoders
    # -------------------------------------------------------------------

    def get_wheel_positions(self) -> tuple:
        """Returns (left_rad, right_rad) cumulative wheel angles in radians."""
        return self.hardware.get_wheel_positions()