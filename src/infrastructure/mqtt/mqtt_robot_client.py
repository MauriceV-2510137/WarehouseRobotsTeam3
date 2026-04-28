import json
import paho.mqtt.client as mqtt

from interfaces.robot_comm import IRobotComm, TaskCallback, AisleCallback
from core.events import TaskReceivedEvent, AisleResponseEvent
from core.task import Task, TaskStatus
from core.pose import Pose

class MqttRobotClient(IRobotComm):

    def __init__(self, robot_id: str, broker_host="localhost") -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        self.robot_id = robot_id
        self.broker_host = broker_host

        self._running = False

        self._on_task_received: TaskCallback | None = None
        self._on_aisle_response: AisleCallback | None = None

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.client.reconnect_delay_set(min_delay=1, max_delay=5)

    # -------------------------
    # Lifecycle
    # -------------------------
    def connect(self) -> None:
        print("[MQTT] Starting async connection...")
        self._running = True
        try:
            self.client.connect_async(self.broker_host)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTT] Initial connection error: {e}")
        
    def disconnect(self) -> None:
        print("[MQTT] Disconnecting...")
        self._running = False
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print(f"[MQTT] Disconnect error: {e}")

    def is_connected(self) -> bool:
        return self.client.is_connected()

    # -------------------------
    # MQTT callbacks
    # -------------------------
    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        if reason_code == 0:
            self._subscribe()
            print("[MQTT] Connected successfully")
        else:
            print(f"[MQTT] Connection failed (rc={reason_code})")

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties) -> None:
        print("[MQTT] Disconnected")

    def _subscribe(self) -> None:
        self.client.subscribe(f"robot/{self.robot_id}/task/assign", qos=1)
        self.client.subscribe(f"robot/{self.robot_id}/aisle/response", qos=1)

    # -------------------------
    # Publish API
    # -------------------------
    def publish_heartbeat(self, task: Task | None, pose: Pose) -> None:
        self.client.publish(
            f"robot/{self.robot_id}/heartbeat",
            json.dumps({
                "task_id": task.id if task else None,
                "pose": [pose.x, pose.y, pose.theta]
            }),
            qos=1,
        )

    def publish_task_status(self, task_id: str, status: TaskStatus, reason: str | None = None) -> None:
        self.client.publish(
            f"robot/{self.robot_id}/task/status",
            json.dumps({
                "task_id": task_id,
                "status": status.name,
                "reason": reason
            }),
            qos=1
        )

    def request_aisle(self, robot_id: str, aisle_id: str, task_id: str) -> None:
        self.client.publish(
            f"aisle/{aisle_id}/request",
            json.dumps({
                "robot_id": robot_id,
                "task_id": task_id
            }),
            qos=1
        )

    def release_aisle(self, robot_id: str, aisle_id: str) -> None:
        self.client.publish(
            f"aisle/{aisle_id}/release",
            json.dumps({
                "robot_id": robot_id
            }),
            qos=1
        )

    # -------------------------
    # Callback registration
    # -------------------------
    def set_task_received_callback(self, callback: TaskCallback) -> None:
        self._on_task_received = callback

    def set_aisle_response_callback(self, callback: AisleCallback) -> None:
        self._on_aisle_response = callback

    # -------------------------
    # MQTT handler
    # -------------------------
    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        
        try:
            payload = json.loads(msg.payload.decode())
        except Exception as e:
            print(f"[MQTT] Invalid JSON: {e}")
            return

        if topic.endswith("task/assign"):
            event = self._parse_task_received_event(payload)
            if self._on_task_received:
                self._on_task_received(event)

        elif topic.endswith("aisle/response"):
            event = self._parse_aisle_response_event(payload)
            if self._on_aisle_response:
                self._on_aisle_response(event)

    # -------------------------
    # Parsing layer
    # -------------------------

    def _parse_aisle_response_event(self, payload: dict) -> AisleResponseEvent:
        return AisleResponseEvent(
            aisle_id=payload["aisle_id"],
            granted=payload["granted"]
        )

    def _parse_task_received_event(self, payload: dict) -> TaskReceivedEvent:
        return TaskReceivedEvent(
            Task(
                id=payload["task_id"],
                aisle_id=payload["aisle_id"],
                aisle_pos=tuple(payload["aisle_pos"]),
                segment_pos=tuple(payload["segment_pos"]),
                base_pos=tuple(payload["base_pos"]),
            )
        )