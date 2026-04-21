
class MotionController:
    def move_forward(self, speed: float):
        raise NotImplementedError

    def rotate(self, speed: float):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError