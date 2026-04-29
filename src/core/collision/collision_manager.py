from enum import Enum, auto

class SafetyState(Enum):
    SAFE  = auto()
    EVADE = auto()   # obstacle is closing in → steer left and crawl
    STOP  = auto()   # critically close → full stop

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------
_STOP_DIST            = 0.15   # m
_EVADE_DIST           = 0.50   # m
_CLOSE_DIST_FALLBACK  = 0.28   # m
_APPROACH_RATE_THRESH = -0.05  # m/s
_EVADE_MIN_DURATION   = 1.5    # s
_EVADE_LINEAR_MAX     = 0.04   # m/s
_EVADE_TURN_LEFT      = 0.8    # rad/s
_ANGULAR_CLAMP        = 1.5    # rad/s


class CollisionManager:
    def __init__(self, sensors) -> None:
        self.sensors = sensors

        self._prev_front: float | None = None
        self._sim_time:   float = 0.0   # accumulated simulation seconds
        self._evade_until: float = 0.0  # simulation-time deadline

        self._last_state: SafetyState = SafetyState.SAFE

    # ------------------------------------------------------------------
    # Primary public interface
    # ------------------------------------------------------------------

    def apply(self, linear: float, angular: float, dt: float) -> tuple[float, float]:
        state = self._compute_state(dt)

        if state == SafetyState.STOP:
            return 0.0, 0.0

        if state == SafetyState.EVADE:
            linear  = min(linear, _EVADE_LINEAR_MAX)
            # Add a left-turn bias on top of whatever the navigator asks for.
            angular = angular + _EVADE_TURN_LEFT
            angular = min(angular, _ANGULAR_CLAMP)
            return linear, angular

        return linear, angular

    def get_state(self) -> SafetyState:
        return self._last_state

    # ------------------------------------------------------------------
    # Internal computation
    # ------------------------------------------------------------------

    def _compute_state(self, dt: float) -> SafetyState:
        front = self.sensors.get_front_distance()

        # --- Advance simulation clock -------------------------------------
        self._sim_time += dt
        now = self._sim_time

        # --- Compute closing rate (m/s) -----------------------------------
        approaching = False
        if self._prev_front is not None and dt > 1e-6:
            rate = (front - self._prev_front) / dt   # negative = closing
            if rate < _APPROACH_RATE_THRESH:
                approaching = True

        self._prev_front = front

        # --- Decision tree ------------------------------------------------

        # Hard stop – obstacle is critically close regardless of approach rate
        if front < _STOP_DIST:
            self._evade_until = max(self._evade_until, now + _EVADE_MIN_DURATION)
            self._last_state = SafetyState.STOP
            return self._last_state

        # Still within a forced evasion window (set by a previous close call)
        if now < self._evade_until:
            self._last_state = SafetyState.EVADE
            return self._last_state

        # Obstacle is closing AND within evasion range -> robot detected
        if front < _EVADE_DIST and approaching:
            self._evade_until = now + _EVADE_MIN_DURATION
            self._last_state = SafetyState.EVADE
            return self._last_state

        # Fallback: anything very close triggers evasion even if rate unclear
        if front < _CLOSE_DIST_FALLBACK:
            self._evade_until = now + _EVADE_MIN_DURATION
            self._last_state = SafetyState.EVADE
            return self._last_state

        self._last_state = SafetyState.SAFE
        return self._last_state

    def is_stop(self) -> bool:
        return self._last_state == SafetyState.STOP

    def is_yield(self) -> bool:
        return self._last_state in (SafetyState.EVADE, SafetyState.STOP)