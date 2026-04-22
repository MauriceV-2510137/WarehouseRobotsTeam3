from controller import Robot as WebotsRobot

from core.robot import Robot

from infrastructure.webots.webots_hardware import WebotsHardware
from infrastructure.webots.webots_motion_controller import WebotsMotionController
from infrastructure.webots.webots_sensors_controller import WebotsSensorsController
from infrastructure.mqtt.mqtt_robot_client import MqttRobotClient

# --- Webots setup ---
webots_robot = WebotsRobot()

hardware = WebotsHardware(webots_robot)
motion = WebotsMotionController(hardware)
sensors = WebotsSensorsController(hardware)
comm = MqttRobotClient("default")

timestep = hardware.get_time_step()

robot = Robot(timestep, motion, sensors, comm)

# --- main loop ---
while webots_robot.step(timestep) != -1:
    robot.update()