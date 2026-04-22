class TelemetryService:
    def __init__(self, robot):
        self.robot = robot

    def publish_heartbeat(self):
        if not self.robot.comm.is_connected():
            return

        task = self.robot.task_manager.get_task()
        self.robot.comm.publish_heartbeat(task, self.robot.pose)