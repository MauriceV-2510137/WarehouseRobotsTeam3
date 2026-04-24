from abc import ABC, abstractmethod

class IMotionController(ABC):
    """Interface for all motion controllers."""

    @abstractmethod
    def move(self, linear: float, angular: float) -> None:
        """Move the robot using combined linear and angular commands."""
        pass

    @abstractmethod
    def stop(self) -> None:
        pass