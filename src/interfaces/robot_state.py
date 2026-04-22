from abc import ABC, abstractmethod

class IRobotState(ABC):
    """Base class for all robot states."""
    
    def on_enter(self, robot) -> None:
        """Optional: Called once when transitioning into this state."""
        pass
        
    def on_exit(self, robot) -> None:
        """Optional: Called once when transitioning out of this state."""
        pass
    
    @abstractmethod
    def update(self, robot) -> 'IRobotState':
        """
        Executes the state's logic.
        Returns:
            - next IRobotState to transition
            - or NoTransition() to remain in current state
        """
        pass