import math
from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import TaskReceivedEvent
from core.task import TaskStatus

TURN_SPEED = 1.5
ANGLE_TOLERANCE = 0.05


class MovingBackToAisleEntryState(IRobotState):

    def __init__(self):
        self._target_angle = None
        self._turning = True

    def on_enter(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return
        # Turn 180° from current heading
        self._target_angle = self._normalize(robot.pose.theta + math.pi)
        self._turning = True
        print(f"Turning 180° then driving to aisle entry: {task.aisle_pos}")

    def on_exit(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        task = robot.task_manager.get_task()
        if not task:
            return TransitionID.MOVE_TO_BASE

        if self._turning:
            angle_error = self._normalize(self._target_angle - robot.pose.theta)
            if abs(angle_error) < ANGLE_TOLERANCE:
                self._turning = False
                robot.motion.stop()
                robot.navigator.set_target(*task.aisle_pos)
            else:
                direction = 1.0 if angle_error > 0 else -1.0
                robot.motion.move(0.0, direction * TURN_SPEED)
        else:
            linear, angular = robot.navigator.compute(robot.pose)
            robot.motion.move(linear, angular)
            if robot.navigator.reached_target():
                robot.navigator.clear_reached()
                return TransitionID.MOVE_TO_BASE

        return TransitionID.NO_TRANSITION

    def _normalize(self, angle: float) -> float:
        return math.atan2(math.sin(angle), math.cos(angle))

    def on_event(self, robot, event):
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")
