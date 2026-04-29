from abc import ABC, abstractmethod

class ISensorsController(ABC):

    @abstractmethod
    def get_scan(self) -> list:
        pass

    @abstractmethod
    def get_front_distance(self) -> float:
        pass

    @abstractmethod
    def get_front_left_distance(self) -> float:
        pass

    @abstractmethod
    def get_front_right_distance(self) -> float:
        pass

    @abstractmethod
    def get_left_distance(self) -> float:
        pass

    @abstractmethod
    def get_right_distance(self) -> float:
        pass

    @abstractmethod
    def get_rear_distance(self) -> float:
        pass
    
    @abstractmethod
    def get_yaw(self) -> float:
        pass

    @abstractmethod
    def get_gyro(self) -> list:
        pass

    @abstractmethod
    def get_accelerometer(self) -> list:
        pass

    @abstractmethod
    def get_wheel_positions(self) -> tuple:
        pass