# Warehouse Robots – Team 3

Autonomous warehouse robot system developed for the course **Software Engineering for Cyber-Physical Systems (2025–2026)**.

**Team:** Jelle Claes · Maurice Vandenheede

---

## Overview

The system coordinates a fleet of autonomous mobile robots (simulated in Webots) that pick items from warehouse shelves and return them to a central base. Three independent tiers communicate over well-defined protocols:

| Tier | Directory | Protocol |
|------|-----------|----------|
| Robot control | `src/` | MQTT |
| Server | `server/` | MQTT + REST + WebSocket |
| Web interface | `webapp/` | REST + WebSocket |

---

## Project Structure

```
src/                        # Robot control (platform-independent)
│  core/                    # State machine, navigation, collision, odometry
│  interfaces/              # IMotionController, ISensorsController, IRobotComm, IRobotState
│  infrastructure/webots/   # Webots-specific implementations
│  bootstrap/               # RobotFactory – dependency injection entry point
│
controllers/                # Webots controller entry point
│
server/                     # FastAPI server
│  core/                    # TaskDispatcher, AisleManager, RobotTracker, TaskStore
│  api/                     # REST endpoints + WebSocket
│  bootstrap/               # Server startup
│
webapp/                     # Single-page web interface (vanilla JS)
│  Index.html
│
worlds/                     # Webots world files
docs/                       # Architecture report, presentation, UML diagrams
tests/                      # Test suite
```

---

## Requirements

- [Webots R2025a](https://cyberbotics.com/)
- Python ≥ 3.10
- An MQTT broker (e.g. [Mosquitto](https://mosquitto.org/))

Install Python dependencies:

```bash
pip install -e .
```

---

## Running the System

### 1. Start the MQTT broker

```bash
mosquitto
```

### 2. Start the server

```bash
python server/app.py
```

The REST API is available at `http://localhost:8000`.  
The web interface is served at `http://localhost:8000` → open `webapp/Index.html` in a browser.

### 3. Open the simulation

Open `worlds/warehouse.wbt` in Webots. The robots connect automatically on startup.

---

## Architecture

Full architecture documentation is available in [`docs/architecture.pdf`](docs/architecture.pdf).  
The presentation is available in [`docs/ArchitecturePresentation.pptx`](docs/ArchitecturePresentation.pptx).  
UML source diagrams (PlantUML) are in [`docs/UML/`](docs/UML/).

### Key design decisions

- **State machine** – 8 states, each with a single responsibility (`on_enter`, `on_exit`, `update(dt)`, `on_event`)
- **Dependency Inversion** – `Robot` depends only on interfaces; `WebotsHardware` + two controllers are the only Webots coupling
- **MQTT QoS=1** – handles WiFi dead spots; wildcard subscriptions scale to N robots
- **Lease-based aisle locking** – 60 s timeout provides crash recovery without extra protocol
- **Closing-rate collision avoidance** – distinguishes moving from stationary obstacles

---

## Tests

A pytest test suite (69 tests) covering the Navigator, OdometryEstimator, CollisionManager, WarehouseMap, AisleManager, and TaskDispatcher is available on the [`tests`](https://github.com/MauriceV-2510137/WarehouseRobotsTeam3/tree/tests) branch. It was not merged into main due to time constraints before the deadline — we did not want to risk breaking anything.

---

## Re-rendering UML Diagrams

```bash
python docs/UML/render.py
```

Requires internet access (uses the PlantUML public server). Output PNGs are written to `docs/UML/`.
