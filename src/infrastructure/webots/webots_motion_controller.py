from interfaces.motion_controller import IMotionController


class WebotsMotionController(IMotionController):
    """
    Converts (linear, angular) velocity commands into individual wheel speeds
    for the TurtleBot3 Burger differential-drive platform.

    Coordinate frame (Webots R2025a, Z-up):
        linear   = forward speed in m/s    (positive = forward along +X)
        angular  = yaw rate in rad/s       (positive = CCW = turning left toward +Y)

    Differential drive formulas (verified for Z-up, X-forward, Y-left):

        v_left  = (linear - angular * L/2) / r
        v_right = (linear + angular * L/2) / r

    Sign check:
        Turning left (angular > 0, CCW):
            v_left  = (v - w*L/2)/r  -> SLOWER  (inner wheel)
            v_right = (v + w*L/2)/r  -> FASTER  (outer wheel)
            Right wheel faster than left  -> robot yaws CCW (+theta)  CORRECT

        Turning right (angular < 0, CW):
            v_left  -> FASTER
            v_right -> SLOWER
            Left wheel faster than right  -> robot yaws CW (-theta)   CORRECT

    The normalisation step scales both wheels proportionally when either would
    exceed max_wheel_speed, preserving the turning ratio.
    """

    def __init__(self, hardware):
        self.hardware = hardware
        self.model    = hardware.model

    def move(self, linear: float, angular: float) -> None:
        """
        Drive the robot at the given linear (m/s) and angular (rad/s) velocity.

        Args:
            linear  : forward speed in m/s  (positive = forward)
            angular : yaw rate in rad/s     (positive = CCW = left turn)
        """
        r = self.model.wheel_radius    # metres
        L = self.model.wheel_base      # metres  (distance between wheel contact patches)

        # --- Differential drive conversion ---
        v_left  = (linear - angular * L / 2.0) / r
        v_right = (linear + angular * L / 2.0) / r

        # --- Proportional normalisation ---
        # If either wheel exceeds the physical limit, scale both by the same
        # factor so the intended turn ratio is preserved.
        max_speed = self.model.max_wheel_speed
        max_val   = max(abs(v_left), abs(v_right))
        if max_val > max_speed:
            scale   = max_speed / max_val
            v_left  *= scale
            v_right *= scale

        self.hardware.set_wheel_velocity(v_left, v_right)

    def stop(self) -> None:
        """Immediately zero both wheel velocities."""
        self.hardware.set_wheel_velocity(0.0, 0.0)