from core.robot import Robot
from core.robot_model import RobotModel
from core.pose import Pose

from infrastructure.webots.webots_hardware import WebotsHardware
from infrastructure.webots.webots_motion_controller import WebotsMotionController
from infrastructure.webots.webots_sensors_controller import WebotsSensorsController
from infrastructure.mqtt.mqtt_robot_client import MqttRobotClient

def _parse_initial_pose(custom_data: str) -> Pose:
    """Parse 'x,y,theta' from the robot's customData field."""
    try:
        parts = [float(v.strip()) for v in custom_data.split(",")]
        return Pose(x=parts[0], y=parts[1], theta=parts[2])
    except Exception:
        return Pose()  # fallback to (0,0,0) if not set

def build_webot_robot(webots_robot) -> Robot:

    # Robot identity
    robot_id = webots_robot.getName()
    initial_pose = _parse_initial_pose(webots_robot.getCustomData())

    # --- configuration ---
    model = RobotModel(
        wheel_radius=0.033,     # metres
        wheel_base=0.160,       # metres
        max_wheel_speed=6.28,   # rad/s
        max_linear_speed=0.20,  # m/s
        max_angular_speed=1.5   # rad/s
    )

    # --- Infrastructure layer (Webots-specific) ---
    hardware = WebotsHardware(webots_robot, model)
    motion = WebotsMotionController(hardware)
    sensors = WebotsSensorsController(hardware)
    comm = MqttRobotClient(robot_id)

    # --- Core robot (no Webots knowledge inside) ---
    return Robot(
        motion=motion,
        sensors=sensors,
        comm=comm,
        model=model,
        initial_pose=initial_pose
    )


def build_actual_robot(robot) -> Robot:
    """
    Placeholder for the real-hardware build path.
    Swap in hardware-specific implementations of IMotionController,
    ISensorsController, and IRobotComm here; the Robot core is unchanged.
    """
    pass