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