from interfaces.robot_state import IRobotState
from core.states.transition_id import TransitionID
from core.events import AisleResponseEvent, TaskReceivedEvent
from core.task import TaskStatus


class WaitingForAisleState(IRobotState):

    def __init__(self) -> None:
        self._transition: bool = False
        self._retry_timer: float = 0.0
        self._retry_interval: float = 2.0  # Seconds between retries
        self._waiting_for_response: bool = False

    def on_enter(self, robot) -> None:
        self._transition = False
        self._retry_timer = 0.0
        self._waiting_for_response = False

        self._send_request(robot)

        robot.motion.stop()

    def on_exit(self, robot) -> None:
        self._transition = False
        self._waiting_for_response = False
        self._retry_timer = 0.0

    def update(self, robot, dt: float) -> TransitionID:
        if self._transition:
            return TransitionID.MOVE_TO_SEGMENT

        if not self._waiting_for_response:
            self._retry_timer += dt

            if self._retry_timer >= self._retry_interval:
                self._retry_timer = 0.0
                self._send_request(robot)

        return TransitionID.NO_TRANSITION

    def on_event(self, robot, event) -> None:
        if isinstance(event, TaskReceivedEvent):
            robot.comm.publish_task_status(
                event.task.id,
                TaskStatus.REJECTED,
                reason="Robot already has active task"
            )
        elif isinstance(event, AisleResponseEvent):
            self._waiting_for_response = False
            if event.granted:
                self._transition = True
            else:
                self._retry_timer = 0.0

    def _send_request(self, robot) -> None:
        task = robot.task_manager.get_task()
        if not task:
            return

        robot.comm.request_aisle(
            robot_id=robot.comm.robot_id,
            aisle_id=task.aisle_id,
            task_id=task.id
        )

        self._waiting_for_response = True