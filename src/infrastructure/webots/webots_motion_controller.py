from interfaces.motion_controller import IMotionController


class WebotsMotionController(IMotionController):
    def __init__(self, hardware) -> None:
        self.hardware = hardware
        self.model = hardware.model

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