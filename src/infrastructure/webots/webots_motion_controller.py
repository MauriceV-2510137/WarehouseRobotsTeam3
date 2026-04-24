from interfaces.motion_controller import IMotionController

class WebotsMotionController(IMotionController):
    def __init__(self, hardware):
        self.hardware = hardware

        self.r = 0.033   # wheel radius
        self.L = 0.160   # wheel base

    def move(self, linear: float, angular: float) -> None:
        # Convert to wheel speeds
        v_left  = (linear - angular * self.L / 2.0) / self.r
        v_right = (linear + angular * self.L / 2.0) / self.r

        # Normalize
        max_speed = self.hardware.max_wheel_speed
        max_val = max(abs(v_left), abs(v_right))

        if max_val > max_speed:
            scale = max_speed / max_val
            v_left *= scale
            v_right *= scale

        self.hardware.set_wheel_velocity(v_left, v_right)

    def stop(self) -> None:
        self.hardware.set_wheel_velocity(0.0, 0.0)