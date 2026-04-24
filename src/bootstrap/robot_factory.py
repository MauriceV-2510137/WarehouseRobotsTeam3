from core.robot import Robot
from core.robot_model import RobotModel

from infrastructure.webots.webots_hardware import WebotsHardware
from infrastructure.webots.webots_motion_controller import WebotsMotionController
from infrastructure.webots.webots_sensors_controller import WebotsSensorsController
from infrastructure.mqtt.mqtt_robot_client import MqttRobotClient

def build_webot_robot(webots_robot):

    # --- configuration ---
    model = RobotModel(
        wheel_radius=0.033,
        wheel_base=0.160,
        max_wheel_speed=6.28,
        max_linear_speed=0.6,
        max_angular_speed=1.5
    )

    # --- Infrastructure layer ---
    hardware = WebotsHardware(webots_robot, model)

    motion = WebotsMotionController(hardware)
    sensors = WebotsSensorsController(hardware)
    comm = MqttRobotClient("default")

    # --- PURE Robot (no knowledge of Webots exists inside it) ---
    return Robot(
        motion=motion,
        sensors=sensors,
        comm=comm,
        model=model
    )


def build_actual_robot(robot):
    # Example of where you would build the real physical robot
    pass