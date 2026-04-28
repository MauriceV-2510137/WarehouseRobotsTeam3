from abc import ABC, abstractmethod
from core.states.transition_id import TransitionID
from core.events import Event

class IRobotState(ABC):
    """Base class for all robot states."""
    
    def on_enter(self, robot) -> None:
        """Called once when transitioning into this state."""
        pass
        
    def on_exit(self, robot) -> None:
        """Called once when transitioning out of this state."""
        pass
    
    @abstractmethod
    def update(self, robot, dt: float) -> TransitionID:
        """Executes the state's logic."""
        pass

    def on_event(self, robot, event: Event) -> None:
        """Handles events"""
        pass