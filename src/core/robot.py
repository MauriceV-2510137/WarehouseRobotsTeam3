from core.odometry import OdometryEstimator
from core.navigator import Navigator
from core.states.state_idle import IdleState

class Robot:
    def __init__(self, motion_controller, sensors):
        self.motion    = motion_controller
        self.sensors   = sensors
        
        self.odometry  = OdometryEstimator()
        self.navigator = Navigator()
        
        self.pose = None
        self.current_state = IdleState()
        self.current_state.on_enter(self)

    def update(self):
        # Update pose
        left_enc, right_enc = self.sensors.get_wheel_positions()
        yaw  = self.sensors.get_yaw()
        self.pose = self.odometry.update(left_enc, right_enc, yaw)

        # Run state
        next_state = self.current_state.update(self)

        # Switch states cleanly if the state requested a change
        if next_state is not self.current_state:
            self.current_state.on_exit(self)
            self.current_state = next_state
            self.current_state.on_enter(self)