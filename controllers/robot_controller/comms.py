"""
comms.py — Server communication layer for the robot.
"""
import json
import logging
import threading
import time
import websocket

log = logging.getLogger(__name__)

class ServerComms:
    RECONNECT_DELAY = 3

    def __init__(self, server_url: str, robot_id: str):
        self.server_url = f"{server_url}/ws/robot/{robot_id}"
        self.robot_id   = robot_id
        self.on_message = None
        self._ws: websocket.WebSocketApp | None = None
        self._connected = False

    def connect(self):
        """Start the background WebSocket thread."""
        t = threading.Thread(target=self._run_forever, daemon=True)
        t.start()

    def _send(self, event: str, data: dict):
        """Send a message directly if connected."""
        if self._connected and self._ws:
            try:
                self._ws.send(json.dumps({"event": event, "data": data}))
            except Exception as e:
                log.warning(f"[{self.robot_id}] Send failed: {e}")

    # --- Public Commands ---
    def send_status(self, status: str): self._send("status_update", {"status": status})
    def send_position(self, pos: dict): self._send("position_update", {"position": pos})
    def request_aisle(self, aisle: int): self._send("request_aisle", {"aisle": aisle})
    def release_aisle(self, aisle: int): self._send("release_aisle", {"aisle": aisle})
    def task_complete(self): self._send("task_complete", {})

    # --- Internal Background Task ---
    def _run_forever(self):
        while True:
            self._ws = websocket.WebSocketApp(
                self.server_url,
                on_open=self._on_open,
                on_message=self._on_message_handler,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            self._ws.run_forever()
            log.info(f"[{self.robot_id}] Reconnecting in {self.RECONNECT_DELAY}s...")
            time.sleep(self.RECONNECT_DELAY)

    def _on_open(self, ws):
        self._connected = True
        log.info(f"[{self.robot_id}] Connected to server")

    def _on_message_handler(self, ws, raw):
        try:
            msg = json.loads(raw)
            if self.on_message:
                self.on_message(msg.get("event", ""), msg.get("data", {}))
        except Exception as e:
            log.error(f"Error parsing message: {e}")

    def _on_error(self, ws, error):
        log.error(f"[{self.robot_id}] WebSocket error: {error}")

    def _on_close(self, ws, code, msg):
        self._connected = False
        log.warning(f"[{self.robot_id}] Disconnected")