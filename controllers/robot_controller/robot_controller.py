from controller import Robot as WebotsRobot

from core.robot import Robot
from core.task import Task
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

# --- Test: Voeg sample orders (tasks) toe ---
robot.task_manager.add_task(Task('move_to_shelf', {'x': -2.0, 'y': 2.3, 'aisle': 1}))
robot.task_manager.add_task(Task('move_to_shelf', {'x': -1.0, 'y': 3.0, 'aisle': 2}))
robot.task_manager.add_task(Task('move_to_shelf', {'x': 0.0, 'y': -2.0, 'aisle': 0}))



# --- main loop ---
while webots_robot.step(timestep) != -1:
    robot.update()