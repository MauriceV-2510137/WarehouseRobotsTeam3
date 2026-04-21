from core.odometry import OdometryEstimator
from core.navigator import Navigator

class Robot:
    def __init__(self, motion_controller, sensors):
        self.motion    = motion_controller
        self.sensors   = sensors
        self.odometry  = OdometryEstimator()
        self.navigator = Navigator()

    def go_to(self, x: float, y: float):
        self.navigator.set_target(x, y)

    def update(self):
        # Update pose
        left_enc, right_enc = self.sensors.get_wheel_positions()
        yaw  = self.sensors.get_yaw()
        pose = self.odometry.update(left_enc, right_enc, yaw)

        # Obstacle check takes priority
        front = self.sensors.get_front_distance()
        if front < 0.5:
            left_d  = self.sensors.get_left_distance()
            right_d = self.sensors.get_right_distance()
            self.motion.rotate(0.6 if left_d > right_d else -0.6)
            return  # skip navigation this tick

        # 3. Navigate toward target
        linear, angular = self.navigator.compute(pose)
        if angular != 0.0:
            self.motion.rotate(angular)
        elif linear != 0.0:
            self.motion.move_forward(linear)
        else:
            self.motion.stop()