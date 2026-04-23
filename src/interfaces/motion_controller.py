from abc import ABC, abstractmethod

class IMotionController(ABC):
    """Interface for all motion controllers."""

    @abstractmethod
    def move_forward(self, speed: float) -> None:
        pass
    
    @abstractmethod
    def rotate(self, speed: float) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def set_wheel_velocities(self, linear: float, angular: float) -> None:
        pass