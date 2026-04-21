from abc import ABC, abstractmethod

class ISensorsController(ABC):

    @abstractmethod
    def get_scan(self):
        pass

    @abstractmethod
    def get_front_distance(self):
        pass

    @abstractmethod
    def get_left_distance(self):
        pass

    @abstractmethod
    def get_right_distance(self):
        pass
    
    @abstractmethod
    def get_yaw(self):
        pass

    @abstractmethod
    def get_gyro(self):
        pass

    @abstractmethod
    def get_accelerometer(self):
        pass

    @abstractmethod
    def get_wheel_positions(self):
        pass