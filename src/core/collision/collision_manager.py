from enum import Enum, auto
import time


class SafetyState(Enum):
    SAFE = auto()
    YIELD = auto()
    STOP = auto()


class CollisionManager:

    def __init__(self, sensors, robot) -> None:
        self.sensors = sensors
        self.robot = robot

        self.stop_distance = 0.10
        self.yield_distance = 0.45

        self._yield_active = False
        self._yield_until = 0.0

        self._min_yield_time = 1.2  # seconds

    def get_state(self) -> SafetyState:

        front = self.sensors.get_front_distance()

        if front < self.stop_distance:
            self._activate_yield()
            return SafetyState.STOP

        if self._yield_active:
            if time.time() < self._yield_until:
                return SafetyState.YIELD
            else:
                self._yield_active = False

        # potential conflict zone
        if front < self.yield_distance:
            return self._resolve_conflict(front)

        return SafetyState.SAFE

    def _resolve_conflict(self, front: float) -> SafetyState:
        my_priority = self.robot.priority

        if my_priority % 2 == 0:
            self._activate_yield(duration=0.6)
            return SafetyState.YIELD

        self._activate_yield(duration=self._min_yield_time)
        return SafetyState.YIELD

    def _activate_yield(self, duration: float | None = None) -> None:
        now = time.time()
        if duration is None:
            duration = self._min_yield_time

        self._yield_active = True
        self._yield_until = max(self._yield_until, now + duration)

    def is_stop(self) -> bool:
        return self.get_state() == SafetyState.STOP

    def is_yield(self) -> bool:
        return self.get_state() == SafetyState.YIELD