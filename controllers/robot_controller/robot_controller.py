from controller import Robot as WebotsRobot
from bootstrap.robot_factory import build_webot_robot
 
webots_robot = WebotsRobot()
timestep = int(webots_robot.getBasicTimeStep())
 
robot = build_webot_robot(webots_robot)
 
prev_time = webots_robot.getTime()
 
while webots_robot.step(timestep) != -1:
    current_time = webots_robot.getTime()
    dt = max(0.0, current_time - prev_time)
    prev_time = current_time
 
    robot.update(dt)