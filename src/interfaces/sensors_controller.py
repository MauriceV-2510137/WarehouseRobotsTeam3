class SensorsController:
    def get_scan(self):
        raise NotImplementedError

    def get_front_distance(self):
        raise NotImplementedError

    def get_yaw(self):
        raise NotImplementedError

    def get_gyro(self):
        raise NotImplementedError

    def get_accelerometer(self):
        raise NotImplementedError

    def get_wheel_positions(self):
        raise NotImplementedError