"""
Central warehouse server.

Responsibilities:
  - Maintain the item queue
  - Track robot states
  - Manage aisle locks (only one robot per aisle at a time)
  - Relay commands to robots and state updates to the web UI

Run with:
    pip install fastapi uvicorn websockets
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import logging
from collections import deque
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Optional
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Warehouse Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class RobotStatus(str, Enum):
    IDLE = "idle"
    MOVING_TO_SHELF = "moving_to_shelf"
    PICKING = "picking"
    RETURNING = "returning"
    WAITING_FOR_AISLE = "waiting_for_aisle"
    OFFLINE = "offline"


@dataclass
class PickTask:
    task_id: str
    item_name: str
    aisle: int          # aisle index (0-based)
    shelf: int          # shelf index within aisle (0-based)
    assigned_to: Optional[str] = None   # robot_id


@dataclass
class RobotState:
    robot_id: str
    status: RobotStatus = RobotStatus.OFFLINE
    current_task: Optional[str] = None  # task_id
    position: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "theta": 0.0})
    aisle_reserved: Optional[int] = None


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

task_queue: deque[PickTask] = deque()
robots: dict[str, RobotState] = {}
aisle_locks: dict[int, str] = {}          # aisle_index -> robot_id holding the lock

# WebSocket connections
robot_connections: dict[str, WebSocket] = {}
ui_connections: list[WebSocket] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(item_name: str, aisle: int, shelf: int) -> PickTask:
    return PickTask(
        task_id=str(uuid.uuid4())[:8],
        item_name=item_name,
        aisle=aisle,
        shelf=shelf,
    )


async def broadcast_ui(event: str, data: dict):
    """Send a JSON event to all connected web UI clients."""
    message = json.dumps({"event": event, "data": data})
    dead = []
    for ws in ui_connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ui_connections.remove(ws)


async def send_robot(robot_id: str, event: str, data: dict):
    """Send a JSON command to a specific robot."""
    ws = robot_connections.get(robot_id)
    if ws is None:
        log.warning("Robot %s not connected, cannot send %s", robot_id, event)
        return
    try:
        await ws.send_text(json.dumps({"event": event, "data": data}))
    except Exception as e:
        log.error("Failed to send to robot %s: %s", robot_id, e)


def full_state_snapshot() -> dict:
    return {
        "robots": {rid: {**asdict(r), "status": r.status.value} for rid, r in robots.items()},
        "queue": [asdict(t) for t in task_queue],
        "aisle_locks": aisle_locks,
    }


async def dispatch_tasks():
    """Assign queued tasks to idle robots."""
    idle_robots = [r for r in robots.values() if r.status == RobotStatus.IDLE]
    while task_queue and idle_robots:
        task = task_queue[0]
        robot = idle_robots.pop(0)
        task.assigned_to = robot.robot_id
        task_queue.popleft()
        robot.status = RobotStatus.MOVING_TO_SHELF
        robot.current_task = task.task_id
        log.info("Dispatching task %s (%s) to robot %s", task.task_id, task.item_name, robot.robot_id)
        await send_robot(robot.robot_id, "assign_task", asdict(task))
        await broadcast_ui("state_update", full_state_snapshot())


# ---------------------------------------------------------------------------
# Aisle lock management  (called by robot messages)
# ---------------------------------------------------------------------------

async def handle_request_aisle(robot_id: str, aisle: int):
    r = robots.get(robot_id)
    if r is None:
        return
    if aisle in aisle_locks:
        # Aisle busy — tell robot to wait
        r.status = RobotStatus.WAITING_FOR_AISLE
        await send_robot(robot_id, "aisle_denied", {"aisle": aisle})
        log.info("Robot %s waiting for aisle %d (held by %s)", robot_id, aisle, aisle_locks[aisle])
    else:
        aisle_locks[aisle] = robot_id
        r.aisle_reserved = aisle
        await send_robot(robot_id, "aisle_granted", {"aisle": aisle})
        log.info("Aisle %d granted to robot %s", aisle, robot_id)
    await broadcast_ui("state_update", full_state_snapshot())


async def handle_release_aisle(robot_id: str, aisle: int):
    if aisle_locks.get(aisle) == robot_id:
        del aisle_locks[aisle]
        r = robots.get(robot_id)
        if r:
            r.aisle_reserved = None
        log.info("Robot %s released aisle %d", robot_id, aisle)
        # Notify waiting robots
        for rid, robot in robots.items():
            if robot.status == RobotStatus.WAITING_FOR_AISLE and robot.current_task:
                task = next((t for t in task_queue if t.task_id == robot.current_task), None)
                # If we can't find it in queue, it was already dispatched
                # Re-try the aisle grant for any waiting robot targeting this aisle
                await send_robot(rid, "retry_aisle", {"aisle": aisle})
                break
    await broadcast_ui("state_update", full_state_snapshot())


# ---------------------------------------------------------------------------
# WebSocket: robots
# ---------------------------------------------------------------------------

@app.websocket("/ws/robot/{robot_id}")
async def robot_ws(websocket: WebSocket, robot_id: str):
    await websocket.accept()
    robot_connections[robot_id] = websocket
    robots[robot_id] = RobotState(robot_id=robot_id, status=RobotStatus.IDLE)
    log.info("Robot %s connected", robot_id)
    await broadcast_ui("state_update", full_state_snapshot())
    await dispatch_tasks()

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            event = msg.get("event")
            data = msg.get("data", {})
            r = robots[robot_id]

            if event == "position_update":
                r.position = data.get("position", r.position)

            elif event == "status_update":
                r.status = RobotStatus(data.get("status", r.status.value))
                log.info("Robot %s -> %s", robot_id, r.status)

            elif event == "request_aisle":
                await handle_request_aisle(robot_id, data["aisle"])
                continue  # broadcast happens inside

            elif event == "release_aisle":
                await handle_release_aisle(robot_id, data["aisle"])

            elif event == "task_complete":
                r.status = RobotStatus.IDLE
                r.current_task = None
                log.info("Robot %s completed task", robot_id)
                await dispatch_tasks()

            await broadcast_ui("state_update", full_state_snapshot())

    except WebSocketDisconnect:
        log.info("Robot %s disconnected", robot_id)
        robots[robot_id].status = RobotStatus.OFFLINE
        robot_connections.pop(robot_id, None)
        # Release any held aisle
        held = [a for a, rid in aisle_locks.items() if rid == robot_id]
        for aisle in held:
            await handle_release_aisle(robot_id, aisle)
        await broadcast_ui("state_update", full_state_snapshot())


# ---------------------------------------------------------------------------
# WebSocket: web UI
# ---------------------------------------------------------------------------

@app.websocket("/ws/ui")
async def ui_ws(websocket: WebSocket):
    await websocket.accept()
    ui_connections.append(websocket)
    log.info("UI client connected (total: %d)", len(ui_connections))
    # Send current state immediately
    await websocket.send_text(json.dumps({"event": "state_update", "data": full_state_snapshot()}))
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            if msg.get("event") == "add_item":
                data = msg["data"]
                task = make_task(data["item_name"], int(data["aisle"]), int(data["shelf"]))
                task_queue.append(task)
                log.info("New task queued: %s (aisle %d, shelf %d)", task.item_name, task.aisle, task.shelf)
                await broadcast_ui("state_update", full_state_snapshot())
                await dispatch_tasks()
    except WebSocketDisconnect:
        ui_connections.remove(websocket)
        log.info("UI client disconnected")


# ---------------------------------------------------------------------------
# REST fallback (useful for testing without a WebSocket client)
# ---------------------------------------------------------------------------

@app.get("/state")
def get_state():
    return full_state_snapshot()


@app.post("/queue")
async def post_queue(item: dict):
    """Add an item to the queue via HTTP POST.
    Body: {"item_name": "...", "aisle": 0, "shelf": 0}
    """
    task = make_task(item["item_name"], int(item["aisle"]), int(item["shelf"]))
    task_queue.append(task)
    await broadcast_ui("state_update", full_state_snapshot())
    await dispatch_tasks()
    return {"task_id": task.task_id}