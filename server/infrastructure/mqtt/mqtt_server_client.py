import json
import paho.mqtt.client as mqtt

from server.interfaces.server_comm import IServerComm, HeartbeatCallback, TaskStatusCallback, AisleRequestCallback, AisleReleaseCallback
from server.core.events import HeartbeatEvent, TaskStatusEvent, AisleRequestEvent, AisleReleaseEvent
from core.task import Task, TaskStatus
from core.pose import Pose

class MqttServerClient(IServerComm):

    def __init__(self, broker_host="localhost") -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        self.broker_host = broker_host

        self._running = True

        self._on_heartbeat: HeartbeatCallback | None = None
        self._on_task_status: TaskStatusCallback | None = None
        self._on_aisle_request: AisleRequestCallback | None = None
        self._on_aisle_release: AisleReleaseCallback | None = None

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
        self.client.subscribe("robot/+/heartbeat", qos=1)
        self.client.subscribe("robot/+/task/status", qos=1)
        self.client.subscribe("aisle/+/request", qos=1)
        self.client.subscribe("aisle/+/release", qos=1)

    # -------------------------
    # Incoming messages
    # -------------------------
    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic

        try:
            payload = json.loads(msg.payload.decode())
        except Exception as e:
            print(f"[MQTT] Invalid JSON: {e}")
            return
        
        if topic.startswith("robot/") and topic.endswith("/heartbeat"):
            event = self._parse_heartbeat(topic, payload)
            if self._on_heartbeat:
                self._on_heartbeat(event)

        elif topic.startswith("robot/") and topic.endswith("/task/status"):
            event = self._parse_task_status(topic, payload)
            if self._on_task_status:
                self._on_task_status(event)

        elif topic.startswith("aisle/") and topic.endswith("/request"):
            event = self._parse_aisle_request(topic, payload)
            if self._on_aisle_request:
                self._on_aisle_request(event)

        elif topic.startswith("aisle/") and topic.endswith("/release"):
            event = self._parse_aisle_release(topic, payload)
            if self._on_aisle_release:
                self._on_aisle_release(event)

    # -------------------------
    # Outgoing
    # -------------------------
    def assign_task(self, robot_id: str, task: Task) -> None:
        self.client.publish(
            f"robot/{robot_id}/task/assign",
            json.dumps({
                "task_id": task.id,
                "aisle_id": task.aisle_id,
                "aisle_pos": task.aisle_pos,
                "segment_pos": task.segment_pos,
                "base_pos": task.base_pos,
            }),
            qos=1
        )

    def respond_aisle(self, robot_id: str, aisle_id: str, granted: bool) -> None:
        self.client.publish(
            f"robot/{robot_id}/aisle/response",
            json.dumps({
                "aisle_id": aisle_id,
                "granted": granted
            }),
            qos=1
        )

    # -------------------------
    # Callback setters
    # -------------------------
    def set_heartbeat_callback(self, cb: HeartbeatCallback) -> None:
        self._on_heartbeat = cb

    def set_task_status_callback(self, cb: TaskStatusCallback) -> None:
        self._on_task_status = cb

    def set_aisle_request_callback(self, cb: AisleRequestCallback) -> None:
        self._on_aisle_request = cb

    def set_aisle_release_callback(self, cb: AisleReleaseCallback) -> None:
        self._on_aisle_release = cb

    # -------------------------
    # Parsing helpers
    # -------------------------
    def _extract_id(self, topic: str, index: int) -> str:
        parts = topic.split("/")
        if len(parts) <= index:
            raise ValueError(f"Invalid topic: {topic}")
        return parts[index]

    # -------------------------
    # Parsing
    # -------------------------
    def _parse_heartbeat(self, topic, payload) -> HeartbeatEvent:
        robot_id = self._extract_id(topic, 1)

        pose = Pose(*payload["pose"])

        return HeartbeatEvent(
            robot_id=robot_id,
            pose=pose,
            task_id=payload["task_id"]
        )

    def _parse_task_status(self, topic, payload) -> TaskStatusEvent:
        robot_id = self._extract_id(topic, 1)

        return TaskStatusEvent(
            robot_id=robot_id,
            task_id=payload["task_id"],
            status=TaskStatus[payload["status"]],
            reason=payload.get("reason")
        )

    def _parse_aisle_request(self, topic, payload) -> AisleRequestEvent:
        aisle_id = self._extract_id(topic, 1)

        return AisleRequestEvent(
            robot_id=payload["robot_id"],
            aisle_id=aisle_id,
            task_id=payload["task_id"]
        )

    def _parse_aisle_release(self, topic, payload) -> AisleReleaseEvent:
        aisle_id = self._extract_id(topic, 1)

        return AisleReleaseEvent(
            robot_id=payload["robot_id"],
            aisle_id=aisle_id
        )