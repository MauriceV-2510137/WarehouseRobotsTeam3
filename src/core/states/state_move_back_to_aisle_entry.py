import math
from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.task import TaskStatus
from core.events import TaskReceivedEvent

class MovingBackToAisleEntryState(IRobotState):

    def on_enter(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return

        robot.reset_collision_state()

        ax, ay = task.aisle_pos
        sx, sy = task.segment_pos
        hx, hy = robot.home

        # Waypoint 1: 0.5m past the aisle entry in the exit direction (clears the aisle in X).
        dx, dy = ax - sx, ay - sy
        dist = math.hypot(dx, dy)
        if dist > 0:
            exit_x = ax + 0.5 * dx / dist
            exit_y = ay + 0.5 * dy / dist
        else:
            exit_x, exit_y = ax, ay

        self._waypoints = [(exit_x, exit_y)]

        # If home is far away in Y, the exit point is in a narrow corridor.
        # Add a diagonal clearing waypoint: go west AND toward home-Y so the robot
        # only needs a small rotation (~33 deg) instead of a full 90 deg turn near the wall.
        hy_diff = hy - exit_y
        if abs(hy_diff) > 1.5:
            clear_x = exit_x - 1.5
            clear_y = exit_y + math.copysign(1.0, hy_diff)
            self._waypoints.append((clear_x, clear_y))
            print(f"Exiting aisle to ({exit_x:.2f}, {exit_y:.2f}) then clearing to ({clear_x:.2f}, {clear_y:.2f})")
        else:
            print(f"Exiting aisle to ({exit_x:.2f}, {exit_y:.2f})")

        robot.navigator.set_target(*self._waypoints.pop(0))

    def on_exit(self, robot) -> None:
        robot.motion.stop()

    def update(self, robot, dt: float) -> TransitionID:
        linear, angular = robot.navigator.compute(robot.pose)
        robot.safe_move(linear, angular, dt)

        if robot.navigator.reached_target():
            robot.navigator.clear_reached()
            if self._waypoints:
                next_wp = self._waypoints.pop(0)
                print(f"[EXIT] pose=({robot.pose.x:.2f},{robot.pose.y:.2f}) theta={robot.pose.theta:.2f} -> next={next_wp}")
                print(f"[EXIT] front={robot.sensors.get_front_distance():.2f} left={robot.sensors.get_left_distance():.2f} right={robot.sensors.get_right_distance():.2f}")
                robot.reset_collision_state()
                robot.navigator.set_target(*next_wp)
                return TransitionID.NO_TRANSITION
            return TransitionID.MOVE_TO_BASE

        return TransitionID.NO_TRANSITION

    def on_event(self, robot, event):
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(event.task.id, TaskStatus.REJECTED, reason="Robot already has active task")
