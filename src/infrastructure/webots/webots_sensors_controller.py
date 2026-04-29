import math
from interfaces.sensors_controller import ISensorsController


class WebotsSensorsController(ISensorsController):

    # -------------------------
    # init
    # -------------------------
    def __init__(self, hardware) -> None:
        self.hardware = hardware
        self._max_range = None

    # -------------------------
    # RAW ACCESS
    # -------------------------
    def get_scan(self) -> list:
        return self.hardware.get_lidar_scan()

    def get_yaw(self) -> float:
        return self.hardware.get_yaw()

    def get_gyro(self) -> list:
        return self.hardware.get_gyro()

    def get_accelerometer(self) -> list:
        return self.hardware.get_accelerometer()

    def get_wheel_positions(self) -> tuple:
        return self.hardware.get_wheel_positions()

    # -------------------------
    # INTERNAL UTILITIES
    # -------------------------
    def _max_range_value(self) -> float:
        if self._max_range is None:
            self._max_range = self.hardware.get_lidar_meta()["range_max"]
        return self._max_range

    def _clean_scan(self, scan: list[float]) -> list[float]:
        max_r = self._max_range_value()
        return [v if math.isfinite(v) else max_r for v in scan]

    def _sector_min(self, scan: list[float], center: int, half_width: int) -> float:
        n = len(scan)
        return min(scan[(center + i) % n] for i in range(-half_width, half_width + 1))

    def _scan(self) -> list[float]:
        return self._clean_scan(self.get_scan())

    # -------------------------
    # SEMANTIC DISTANCES
    # -------------------------
    def _distance_at(self, center_fraction: float) -> float:
        scan = self._scan()
        n = len(scan)
        center = round(center_fraction * n) % n
        return self._sector_min(scan, center, n // 24)

    def get_front_distance(self) -> float:
        return self._distance_at(0.5)

    def get_rear_distance(self) -> float:
        return self._distance_at(0.0)

    def get_left_distance(self) -> float:
        return self._distance_at(0.75)

    def get_right_distance(self) -> float:
        return self._distance_at(0.25)