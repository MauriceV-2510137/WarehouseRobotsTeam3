import json
import paho.mqtt.client as mqtt

from server.interfaces.server_comm import IServerComm
from server.core.events import HeartbeatEvent, TaskStatusEvent, AisleRequestEvent, TaskStatus
from core.pose import Pose
from core.task import Task

class MqttServerClient(IServerComm):

    def __init__(self, broker_host="localhost"):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        self.broker_host = broker_host

        self._connected = False
        self._running = True

        self._on_heartbeat = None
        self._on_aisle_request = None
        self._on_task_status = None

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.client.reconnect_delay_set(min_delay=1, max_delay=5)

    # -------------------------
    # Lifecycle
    # -------------------------
    def connect(self):
        print("[MQTT] Starting async connection...")
        self._running = True
        try:
            self.client.connect_async(self.broker_host)
            self.client.loop_start()
        except Exception as e:
            self._connected = False
            print(f"[MQTT] Initial connection error: {e}")

    def disconnect(self):
        print("[MQTT] Disconnecting...")
        self._running = False
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print(f"[MQTT] Disconnect error: {e}")

    def is_connected(self) -> bool:
        return self._connected

    # -------------------------
    # MQTT callbacks
    # -------------------------
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            self._subscribe()
            print("[MQTT] Connected successfully")
        
        else:
            self._connected = False
            print(f"[MQTT] Connection failed (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        print("[MQTT] Disconnected")

    def _subscribe(self):
        self.client.subscribe("robot/+/heartbeat")
        self.client.subscribe("robot/+/task/status")
        self.client.subscribe("aisle/+/request")

    # -------------------------
    # Incoming messages -> callbacks
    # -------------------------
    def _on_message(self, client, userdata, msg):
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
            event = self._parse_aisle_request(payload)
            if self._on_aisle_request:
                self._on_aisle_request(event)

    # -------------------------
    # Outgoing
    # -------------------------
    def assign_task(self, robot_id: str, task: Task):
        self.client.publish(
            f"robot/{robot_id}/task/assign",
            json.dumps({
                "task_id": task.id,
                "aisle_id": task.aisle_id,
                "aisle_pos": task.aisle_pos,
                "segment_pos": task.segment_pos,
                "base_pos": task.base_pos,
            })
        )

    def respond_aisle(self, robot_id, aisle_id, granted):
        self.client.publish(
            f"robot/{robot_id}/aisle/response",
            json.dumps({
                "aisle_id": aisle_id,
                "granted": granted
            })
        )

    # -------------------------
    # Callback setters
    # -------------------------
    def set_heartbeat_callback(self, cb):
        self._on_heartbeat = cb

    def set_aisle_request_callback(self, cb):
        self._on_aisle_request = cb

    def set_task_status_callback(self, cb):
        self._on_task_status = cb


    # -------------------------
    # Parsing
    # -------------------------
    def _parse_heartbeat(self, topic, payload):
        robot_id = topic.split("/")[1]

        pose = Pose(*payload["pose"])

        return HeartbeatEvent(
            robot_id=robot_id,
            pose=pose,
            task_id=payload["task_id"]
        )

    def _parse_task_status(self, topic, payload):
        robot_id = topic.split("/")[1]

        return TaskStatusEvent(
            robot_id=robot_id,
            task_id=payload["task_id"],
            status=TaskStatus[payload["status"]],
            reason=payload.get("reason")
        )

    def _parse_aisle_request(self, payload):
        return AisleRequestEvent(
            robot_id=payload["robot_id"],
            aisle_id=payload["aisle_id"],
            task_id=payload["task_id"]
        )