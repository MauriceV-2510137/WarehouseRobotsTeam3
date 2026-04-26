# Warehouse Robots – Team 3

Simulatie van autonome magazijnrobots in Webots met een centrale server via MQTT.

---

## Vereisten

| Software | Versie | Download |
|---|---|---|
| Python | ≥ 3.10 | python.org |
| Webots | R2025a | cyberbotics.com |
| Mosquitto (MQTT broker) | ≥ 2.0 | mosquitto.org |

Installeer de Python-afhankelijkheden vanuit de projectroot:

```powershell
pip install -e .
```

---

## Projectstructuur

```
WarehouseRobotsTeam3/
├── controllers/
│   └── robot_controller/
│       └── robot_controller.py   # Webots entry point voor de robot
├── server/
│   ├── app.py                    # Server entry point
│   ├── core/
│   │   ├── server.py             # Centrale serverlogica
│   │   ├── aisle_manager.py      # Beheert gangtoegang (locking)
│   │   └── robot_registry.py     # Bijhoudt status van alle robots
│   └── infrastructure/
│       └── mqtt/
│           └── mqtt_server_client.py
├── src/
│   └── core/                     # Robotlogica (geen Webots-afhankelijkheden)
│       ├── robot.py
│       ├── navigator.py
│       ├── task.py
│       └── states/               # Toestandsmachine (8 states)
└── worlds/
    └── warehouse.wbt             # Webots wereld
```

---

## Magazijn lay-out

```
y = +4.3  ╔══════════════════════════════╗
y = +4    ║  corridor (north)            ║
y = +3    ║  [rek: aisle_left_2]         ║
y = +2    ║  corridor (center_north)     ║
y = +1    ║  [rek: aisle_left]           ║
y =  0    ║  corridor (center)           ║
y = -1    ║  [rek: aisle_right]          ║
y = -2    ║  corridor (center_south)     ║
y = -3    ║  [rek: aisle_right_2]        ║
y = -4    ║  corridor (south)            ║
y = -4.3  ╚══════════════════════════════╝
           x=0   x=3  x=4      x=7
           robot  ↑             ↑
                  aisle entry   einde gang

Robot startpositie: (0, 0)
Aisles beginnen bij x = 4, entry punt x = 3
```

---

## Stap-voor-stap: simulatie opstarten

### Stap 1 – MQTT broker starten

Open een terminal en start Mosquitto:

```powershell
& "C:\Program Files\mosquitto\mosquitto.exe"
```

Laat deze terminal open. De broker luistert op `localhost:1883`.

---

### Stap 2 – Centrale server starten

Open een **tweede terminal** vanuit de projectroot:

```powershell
cd C:\IIW\SoftwareEngineeringForCyber-PhysicalSystems\WarehouseRobotsTeam3
python -m server.app
```

Verwachte output:
```
[MQTT] Starting async connection...
[MQTT] Connected successfully
```

De server luistert nu op heartbeats, taakstatussen en gangtoegangsverzoeken van robots.

---

### Stap 3 – Webots simulator starten

1. Open Webots
2. Laad het bestand `worlds/warehouse.wbt`
3. Start de simulatie (play-knop)

De robot (`robot_id = "default"`) verbindt automatisch via MQTT. In de serverterminal verschijnt:

```
[RobotRegistry] Registered robot: default
[default] pose=Pose(x=0.0, y=0.0, theta=0.0)
```

---

### Stap 4 – Een taak toewijzen

Open een **derde terminal** vanuit de projectroot en wijs een taak toe:

```powershell
cd C:\IIW\SoftwareEngineeringForCyber-PhysicalSystems\WarehouseRobotsTeam3
python -m server.assign_task <gang>
```

Beschikbare gangen:

| Gang | aisle_pos | segment_pos |
|---|---|---|
| `south` | (3, -4) | (6.5, -4) |
| `center_south` | (3, -2) | (6.5, -2) |
| `center` | (3, 0) | (6.5, 0) |
| `center_north` | (3, 2) | (6.5, 2) |
| `north` | (3, 4) | (6.5, 4) |

Voorbeeld:
```powershell
python -m server.assign_task center_south
```

Optioneel een eigen task-id meegeven:
```powershell
python -m server.assign_task south task_42
```

---

### Stap 5 – Robot volgen

In de **serverterminal** zie je de voortgang van de robot:

```
[default] task=task_1 -> TaskStatus.IN_PROGRESS
[AisleManager] Robot default locked aisle center_south (expires in 300s)
[AisleManager] GRANTED aisle center_south to robot default
[default] pose=Pose(x=1.23, y=-0.01, theta=0.02)
...
[AisleManager] Released lock on aisle center_south (was held by default)
[default] task=task_1 -> TaskStatus.DONE
```

In het **assign_task script** zie je de statusupdates live binnenkomen.

---

## Robot toestandsmachine

De robot doorloopt de volgende states voor elke taak:

```
WAIT_CONNECTION
      ↓  (verbinding gemaakt)
    IDLE
      ↓  (taak ontvangen)
MOVE_TO_AISLE_ENTRY
      ↓  (aisle entry bereikt)
WAIT_FOR_AISLE_ACCESS
      ↓  (gang vrij)
MOVE_TO_SEGMENT
      ↓  (segment bereikt)
PICKUP_ITEM
      ↓  (item gepakt)
MOVE_BACK_TO_AISLE_ENTRY
      ↓  (entry bereikt)
MOVE_TO_BASE
      ↓  (basis bereikt)
    IDLE
```

---

## Robot Registry

De server houdt automatisch de status bij van elke robot die verbindt:

| Veld | Beschrijving |
|---|---|
| `status` | `IDLE`, `BUSY` of `DISCONNECTED` |
| `pose` | Laatste bekende positie (x, y, theta) |
| `current_task_id` | Actieve taak-ID |
| `current_aisle_id` | Gang die momenteel bezet is |
| `last_heartbeat` | Tijdstip van laatste heartbeat |

Een robot wordt automatisch als `DISCONNECTED` beschouwd als er 30 seconden geen heartbeat binnenkomt.

---

## Unit tests uitvoeren

Vanuit de **projectroot**:

```powershell
cd C:\IIW\SoftwareEngineeringForCyber-PhysicalSystems\WarehouseRobotsTeam3
python -m pytest server/test_robot_registry.py -v
```

Voor alle tests:

```powershell
python -m pytest -v
```

---

## MQTT berichtformaten

### Heartbeat (robot → server)
**Topic:** `robot/{robot_id}/heartbeat`
```json
{
  "pose": [x, y, theta],
  "task_id": "task_1"
}
```

### Taak toewijzen (server → robot)
**Topic:** `robot/{robot_id}/task/assign`
```json
{
  "task_id": "task_1",
  "aisle_id": "center_south",
  "aisle_pos": [3.0, -2.0],
  "segment_pos": [6.5, -2.0],
  "base_pos": [0.0, 0.0]
}
```

### Taakstatus (robot → server)
**Topic:** `robot/{robot_id}/task/status`
```json
{
  "task_id": "task_1",
  "status": "DONE",
  "reason": null
}
```

### Gangtoegang aanvragen (robot → server)
**Topic:** `aisle/{aisle_id}/request`
```json
{
  "robot_id": "default",
  "aisle_id": "center_south",
  "task_id": "task_1"
}
```

### Gangtoegang antwoord (server → robot)
**Topic:** `robot/{robot_id}/aisle/response`
```json
{
  "aisle_id": "center_south",
  "granted": true
}
```
