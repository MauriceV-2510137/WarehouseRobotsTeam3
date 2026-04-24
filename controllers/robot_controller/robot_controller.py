from controller import Robot as WebotsRobot
from bootstrap.robot_factory import build_webot_robot

webots_robot = WebotsRobot()

robot = build_webot_robot(webots_robot)
timestep = int(webots_robot.getBasicTimeStep())

while webots_robot.step(timestep) != -1:
    robot.update(timestep / 1000.0) # convert webots ms timestep to seconds