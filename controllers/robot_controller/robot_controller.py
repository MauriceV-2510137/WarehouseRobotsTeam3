import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

from controller import Robot as WebotsRobot

from src.infrastructure.webots.webots_hardware import WebotsHardware
from src.infrastructure.webots.webots_motion_controller import WebotsMotionController
from src.infrastructure.webots.webots_sensors_controller import WebotsSensorsController
from src.core.robot import Robot

# --- Webots setup ---
webots_robot = WebotsRobot()

hardware = WebotsHardware(webots_robot)
motion = WebotsMotionController(hardware)
sensors = WebotsSensorsController(hardware)
robot = Robot(motion, sensors)

timestep = hardware.get_time_step()

# --- main loop ---
while webots_robot.step(timestep) != -1:
    robot.update()