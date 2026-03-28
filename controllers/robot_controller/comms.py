"""
comms.py — Server communication layer for the robot.

This module is the ONLY place that knows about WebSockets and the
server protocol.  robot_controller.py depends on this interface, not
on any concrete transport, making it easy to swap WebSockets for MQTT
or any other protocol without touching navigation or state-machine code.

Usage:
    comms = ServerComms("ws://localhost:8000", "robot0")
    comms.on_message = my_handler   # fn(event: str, data: dict)
    comms.connect()                 # starts background thread
    comms.send_status("idle")
"""

import json
import logging
import threading
import time

import websocket  # pip install websocket-client

log = logging.getLogger(__name__)


class ServerComms:
    """
    Manages a persistent WebSocket connection to the central server.
    Incoming messages are dispatched to `self.on_message(event, data)`.
    Outgoing messages are queued and sent from the background thread.
    """

    RECONNECT_DELAY = 3   # seconds between reconnect attempts

    def __init__(self, server_url: str, robot_id: str):
        self.server_url = f"{server_url}/ws/robot/{robot_id}"
        self.robot_id   = robot_id
        self.on_message = None        # set by controller
        self._ws: websocket.WebSocketApp | None = None
        self._send_queue: list[str] = []
        self._lock = threading.Lock()
        self._connected = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def connect(self):
        """Start the background WebSocket thread (non-blocking)."""
        t = threading.Thread(target=self._run_forever, daemon=True)
        t.start()

    def send_status(self, status: str):
        self._enqueue("status_update", {"status": status})

    def send_position(self, position: dict):
        self._enqueue("position_update", {"position": position})

    def request_aisle(self, aisle: int):
        self._enqueue("request_aisle", {"aisle": aisle})

    def release_aisle(self, aisle: int):
        self._enqueue("release_aisle", {"aisle": aisle})

    def task_complete(self):
        self._enqueue("task_complete", {})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _enqueue(self, event: str, data: dict):
        msg = json.dumps({"event": event, "data": data})
        with self._lock:
            self._send_queue.append(msg)

    def _flush_queue(self):
        with self._lock:
            items, self._send_queue = self._send_queue[:], []
        for msg in items:
            try:
                self._ws.send(msg)
            except Exception as e:
                log.warning("Send failed: %s", e)
                with self._lock:
                    self._send_queue.insert(0, msg)   # re-queue
                break

    def _on_open(self, ws):
        self._connected = True
        log.info("[%s] Connected to server", self.robot_id)

    def _on_message(self, ws, raw):
        try:
            msg = json.loads(raw)
            event = msg.get("event", "")
            data  = msg.get("data", {})
            if self.on_message:
                self.on_message(event, data)
        except Exception as e:
            log.error("Error handling message: %s", e)

    def _on_error(self, ws, error):
        log.error("[%s] WebSocket error: %s", self.robot_id, error)

    def _on_close(self, ws, code, msg):
        self._connected = False
        log.warning("[%s] Disconnected (code=%s)", self.robot_id, code)

    def _run_forever(self):
        """Keep reconnecting on failure."""
        while True:
            self._ws = websocket.WebSocketApp(
                self.server_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            # run_forever blocks; we override dispatcher to flush our queue
            self._ws.run_forever()
            log.info("[%s] Reconnecting in %ds …", self.robot_id, self.RECONNECT_DELAY)
            time.sleep(self.RECONNECT_DELAY)

    def _dispatcher(self, read_list, write_list, except_list):
        """Custom dispatcher so we can inject outgoing messages."""
        import select
        r, _w, _e = select.select(read_list, write_list, except_list, 0.05)
        self._flush_queue()
        return r, _w, _e