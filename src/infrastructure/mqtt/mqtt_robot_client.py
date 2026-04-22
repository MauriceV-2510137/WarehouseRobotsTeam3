import json
import paho.mqtt.client as mqtt

from interfaces.robot_comm import IRobotComm, TaskCallback, AisleCallback
from core.task import Task
from core.pose import Pose
from core.events import TaskReceivedEvent, AisleResponseEvent

class MqttRobotClient(IRobotComm):

    def __init__(self, robot_id: str, broker_host="localhost"):
        self.robot_id = robot_id
        self.broker_host = broker_host

        self.client = mqtt.Client()
        self._connected = False

        self._on_task_received: TaskCallback | None = None
        self._on_aisle_response: AisleCallback | None = None

        # MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    # -------------------------
    # Connection
    # -------------------------
    def connect(self):
        print("[MQTT] Starting async connection...")
        try:
            self.client.connect_async(self.broker_host)
            self.client.loop_start()
        except Exception as e:
            self._connected = False
            print(f"[MQTT] Initial connection error: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print("[MQTT] Connected successfully")
            self.subscribe()
        else:
            self._connected = False
            print(f"[MQTT] Connection failed (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        print("[MQTT] Disconnected")

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self):
        self.client.subscribe(f"robot/{self.robot_id}/task/assign")
        self.client.subscribe(f"robot/{self.robot_id}/aisle/response")

    # -------------------------
    # Publish API
    # -------------------------
    def publish_task_status(self, task_id, status, reason=None):
        payload = {
            "task_id": task_id,
            "status": status,
            "reason": reason
        }

        self.client.publish(
            f"robot/{self.robot_id}/task/status",
            json.dumps(payload),
            qos=1
        )

    def request_aisle(self, robot_id, aisle_id, task_id):
        payload = {
            "robot_id": robot_id,
            "aisle_id": aisle_id,
            "task_id": task_id
        }

        self.client.publish(
            f"robot/{robot_id}/aisle/request",
            json.dumps(payload),
            qos=1
        )

    def publish_heartbeat(self, task: Task, pose: Pose):
        self.client.publish(
            f"robot/{self.robot_id}/heartbeat",
            json.dumps({
                "task_id": task.id if task else None,
                "pose": [pose.x, pose.y, pose.theta]
            }),
            qos=1,
            retain=True
        )

    # -------------------------
    # Callback registration
    # -------------------------
    def set_on_task_received(self, callback: TaskCallback) -> None:
        self._on_task_received = callback

    def set_on_aisle_response(self, callback: AisleCallback) -> None:
        self._on_aisle_response = callback

    # -------------------------
    # MQTT handler
    # -------------------------
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if topic.endswith("task/assign"):
            task = self._parse_task(payload)
            event = TaskReceivedEvent(task)

            if self._on_task_received:
                self._on_task_received(event)

        elif topic.endswith("aisle/response"):
            event = AisleResponseEvent(
                aisle_id=payload["aisle_id"],
                granted=payload["granted"]
            )

            if self._on_aisle_response:
                self._on_aisle_response(event)

    # -------------------------
    # Parsing layer
    # -------------------------
    def _parse_task(self, payload: dict) -> Task:
        return Task(
            id=payload["task_id"],
            shelf_x=payload["shelf"][0],
            shelf_y=payload["shelf"][1],
            base_x=payload["base"][0],
            base_y=payload["base"][1],
        )