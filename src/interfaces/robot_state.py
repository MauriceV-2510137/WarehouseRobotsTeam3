from abc import ABC, abstractmethod

class IRobotState(ABC):
    """Base class for all robot states."""
    
    @abstractmethod
    def update(self, robot) -> 'IRobotState':
        """
        Executes the state's logic.
        Returns the NEXT state, or `self` if it should remain in this state.
        """
        pass
        
    def on_enter(self, robot):
        """Optional: Called once when transitioning into this state."""
        pass
        
    def on_exit(self, robot):
        """Optional: Called once when transitioning out of this state."""
        pass