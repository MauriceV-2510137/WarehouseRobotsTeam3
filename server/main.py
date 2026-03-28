import json
import logging
import uuid
from collections import deque
from dataclasses import dataclass, asdict, field
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Warehouse Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@dataclass
class Task:
    task_id: str
    item_name: str
    aisle: int
    assigned_to: Optional[str] = None

@dataclass
class RobotState:
    robot_id: str
    status: str = "offline"
    current_task: Optional[str] = None
    position: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "theta": 0.0})
    aisle_reserved: Optional[int] = None

task_queue: deque[Task] = deque()
robots: dict[str, RobotState] = {}
aisle_locks: dict[int, str] = {}
robot_connections: dict[str, WebSocket] = {}
ui_connections: list[WebSocket] = []

def _snapshot() -> dict:
    return {
        "robots": {rid: asdict(r) for rid, r in robots.items()},
        "queue": [asdict(t) for t in task_queue],
        "aisle_locks": aisle_locks,
    }

async def _broadcast_ui():
    msg = json.dumps({"event": "state_update", "data": _snapshot()})
    for ws in list(ui_connections):
        try: await ws.send_text(msg)
        except: ui_connections.remove(ws)

async def _send_robot(robot_id: str, event: str, data: dict):
    ws = robot_connections.get(robot_id)
    if ws:
        try: await ws.send_text(json.dumps({"event": event, "data": data}))
        except Exception as e: log.error(f"Send to {robot_id} failed: {e}")

async def _dispatch():
    idle = [r for r in robots.values() if r.status == "idle"]
    while task_queue and idle:
        task = task_queue.popleft()
        robot = idle.pop(0)
        task.assigned_to = robot.robot_id
        robot.status = "moving"
        robot.current_task = task.task_id
        await _send_robot(robot.robot_id, "assign_task", asdict(task))
    await _broadcast_ui()

async def _request_aisle(robot_id: str, aisle: int):
    r = robots.get(robot_id)
    if not r: return
    if aisle in aisle_locks:
        r.status = "waiting_for_aisle"
        await _send_robot(robot_id, "aisle_denied", {"aisle": aisle})
    else:
        aisle_locks[aisle] = robot_id
        r.aisle_reserved = aisle
        r.status = "moving"
        await _send_robot(robot_id, "aisle_granted", {"aisle": aisle})
    await _broadcast_ui()

async def _release_aisle(robot_id: str, aisle: int):
    if aisle_locks.get(aisle) != robot_id: return
    del aisle_locks[aisle]
    if r := robots.get(robot_id):
        r.aisle_reserved = None

    # Fix: Notify ALL waiting robots so they retry their respective target aisles
    for rid, robot in robots.items():
        if robot.status == "waiting_for_aisle":
            await _send_robot(rid, "retry_aisle", {})
    await _broadcast_ui()

@app.websocket("/ws/robot/{robot_id}")
async def robot_ws(ws: WebSocket, robot_id: str):
    await ws.accept()
    robot_connections[robot_id] = ws
    robots[robot_id] = RobotState(robot_id=robot_id, status="idle")
    await _dispatch()

    try:
        while True:
            msg = json.loads(await ws.receive_text())
            event, data = msg.get("event"), msg.get("data", {})
            r = robots[robot_id]

            if event == "position_update":
                r.position = data.get("position", r.position)
            elif event == "status_update":
                r.status = data.get("status", r.status)
            elif event == "request_aisle":
                await _request_aisle(robot_id, int(data["aisle"]))
            elif event == "release_aisle":
                await _release_aisle(robot_id, int(data["aisle"]))
            elif event == "task_complete":
                r.status = "idle"
                r.current_task = None
                await _dispatch()

            if event == "position_update":
                await _broadcast_ui() # Keep UI fast
    except WebSocketDisconnect:
        robots[robot_id].status = "offline"
        robot_connections.pop(robot_id, None)
        for aisle in [a for a, rid in aisle_locks.items() if rid == robot_id]:
            await _release_aisle(robot_id, aisle)
        await _broadcast_ui()

@app.websocket("/ws/ui")
async def ui_ws(ws: WebSocket):
    await ws.accept()
    ui_connections.append(ws)
    await _broadcast_ui()
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            if msg.get("event") == "add_item":
                d = msg["data"]
                task_queue.append(Task(str(uuid.uuid4())[:8], d["item_name"], int(d["aisle"])))
                await _dispatch()
    except WebSocketDisconnect:
        ui_connections.remove(ws)