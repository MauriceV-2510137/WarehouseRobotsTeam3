from src.interfaces.motion_controller import MotionController

class WebotsMotionController(MotionController):
    def __init__(self, hardware):
        self.hardware = hardware

    def _scale(self, speed: float):
        # clamp to [-1, 1]
        speed = max(-1.0, min(1.0, speed))
        return speed * self.hardware.max_wheel_speed

    def move_forward(self, speed: float):
        v = self._scale(speed)
        self.hardware.set_wheel_velocity(v, v)

    def rotate(self, speed: float):
        v = self._scale(speed)
        self.hardware.set_wheel_velocity(-v, v)

    def stop(self):
        self.hardware.set_wheel_velocity(0.0, 0.0)