# Warehouse Robot System — Prototype

4487 Software Engineering for Cyberphysical Systems, 2025-2026

## Folder structure

```
root/
├── robots/
│   ├── robot_controller.py   # Webots robot controller (state machine)
│   ├── comms.py              # WebSocket client — only file that knows about networking
│   └── navigation.py         # Proportional waypoint follower — no Webots imports
├── server/
│   └── main.py               # FastAPI server: queue, aisle locks, WebSocket hub
├── simulation/
│   └── warehouse.wbt         # Webots world: 3 aisles × 3 shelves, 3 TurtleBots
├── webapp/
│   └── index.html            # Single-file dashboard (no build step needed)
├── tests/
│   └── test_warehouse.py     # pytest tests for server logic and navigation
└── requirements.txt
```

## Architecture overview

```
┌─────────────┐   WebSocket /ws/robot/{id}   ┌────────────────┐
│  Robot 0    │ ◄────────────────────────────► │                │
│  Robot 1    │ ◄────────────────────────────► │  Central       │
│  Robot 2    │ ◄────────────────────────────► │  Server        │
└─────────────┘                                │  (FastAPI)     │
  Webots sim                                   │                │
                                               │  - Item queue  │
┌─────────────┐   WebSocket /ws/ui            │  - Aisle locks │
│  Web UI     │ ◄────────────────────────────► │  - Robot state │
│  (browser)  │                                └────────────────┘
└─────────────┘
```

**Key design decisions:**
- `comms.py` is the only file with knowledge of WebSockets. Swapping to MQTT means only changing this file.
- `navigation.py` has no Webots imports — it can be unit tested and reused on real hardware.
- The server is a single source of truth. Robots are stateless clients: if a robot restarts, it reconnects and receives its next task normally.
- Aisle locking is centralised on the server, not negotiated between robots, avoiding distributed consensus complexity.

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the server

```bash
cd server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open the web UI

Open `webapp/index.html` in a browser (or serve it with any static file server).

```bash
cd webapp
python -m http.server 3000
# then open http://localhost:3000
```

### 4. Run the simulation

1. Open Webots.
2. Open `simulation/warehouse.wbt`.
3. Set the controller for each TurtleBot to `robot_controller` (pointing to `robots/robot_controller.py`).
4. Make sure `comms.py` and `navigation.py` are in the same directory as `robot_controller.py`.
5. Press Play — robots will connect to the server automatically.

### 5. Add items to pick

In the web UI, type an item name, set the aisle (0–2) and shelf (0–2), and click **Add to queue**.  
An idle robot will be assigned the task immediately.

### 6. Run tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Adjusting the warehouse layout

If you change shelf positions in the Webots world, update the matching dictionaries in `robots/robot_controller.py`:

- `SHELF_POSITIONS` — `(aisle, shelf) -> (world_x, world_y)`
- `AISLE_ENTRY` — `aisle -> (world_x, world_y)` where the robot waits before entering
- `HOME_POSITIONS` — per-robot home pose

The server does not need to know about physical positions — it only deals with aisle indices.

## Next steps for the final system

- Replace the proportional controller in `navigation.py` with a proper SLAM / path-planning stack (e.g. integrate a SLAM library for map building and A* for routing).
- Add collision detection / replanning (currently robots avoid each other only via aisle locks).
- Persist the item queue to a database (SQLite or PostgreSQL) so the server can restart without losing state.
- Add authentication to the web UI.
- Replace `WoodenBox` shelf proxies in the Webots world with proper shelf models.