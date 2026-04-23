from interfaces.motion_controller import IMotionController

class WebotsMotionController(IMotionController):
    def __init__(self, hardware):
        self.hardware = hardware

    def _scale(self, speed: float):
        # clamp to [-1, 1]
        speed = max(-1.0, min(1.0, speed))
        return speed * self.hardware.max_wheel_speed

    def move_forward(self, speed: float) -> None:
        v = self._scale(speed)
        self.hardware.set_wheel_velocity(v, v)

    def rotate(self, speed: float) -> None:
        v = self._scale(speed)
        self.hardware.set_wheel_velocity(-v, v)

    def stop(self) -> None:
        self.hardware.set_wheel_velocity(0.0, 0.0)

    def set_wheel_velocities(self, linear: float, angular: float) -> None:
        # Differential drive kinematics
        wheel_base = 0.1
        v_left = linear - (angular * wheel_base / 2)
        v_right = linear + (angular * wheel_base / 2)
        
        # Scale to valid range
        v_left = self._scale(v_left)
        v_right = self._scale(v_right)
        
        self.hardware.set_wheel_velocity(v_left, v_right)