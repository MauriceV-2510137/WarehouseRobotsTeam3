"""
Simulates 3 robots sending heartbeats, task statuses and aisle requests.
Run AFTER starting mosquitto and the server.

Usage:
    cd C:\IIW\SoftwareEngineeringForCyber-PhysicalSystems\WarehouseRobotsTeam3
    python -m server.test_registry_mqtt
"""
import json
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER)
client.loop_start()

time.sleep(0.5)  # wait for connection


def heartbeat(robot_id, x, y, theta, task_id=None):
    payload = json.dumps({"pose": [x, y, theta], "task_id": task_id})
    client.publish(f"robot/{robot_id}/heartbeat", payload)
    print(f"[SENT] heartbeat {robot_id} pose=({x},{y}) task={task_id}")


def task_status(robot_id, task_id, status):
    payload = json.dumps({"task_id": task_id, "status": status, "reason": None})
    client.publish(f"robot/{robot_id}/task/status", payload)
    print(f"[SENT] task_status {robot_id} task={task_id} -> {status}")


def aisle_request(robot_id, aisle_id, task_id):
    payload = json.dumps({"robot_id": robot_id, "aisle_id": aisle_id, "task_id": task_id})
    client.publish(f"aisle/{aisle_id}/request", payload)
    print(f"[SENT] aisle_request {robot_id} aisle={aisle_id}")


print("\n--- Stap 1: 3 robots sturen heartbeat (IDLE) ---")
heartbeat("robot_1", x=0.0, y=0.0, theta=0.0)
heartbeat("robot_2", x=1.0, y=0.5, theta=0.5)
heartbeat("robot_3", x=2.0, y=1.0, theta=1.0)
time.sleep(1)

print("\n--- Stap 2: robot_1 en robot_2 krijgen een taak ---")
heartbeat("robot_1", x=0.1, y=0.1, theta=0.0, task_id="task_1")
heartbeat("robot_2", x=1.1, y=0.6, theta=0.5, task_id="task_2")
heartbeat("robot_3", x=2.0, y=1.0, theta=1.0)  # still idle
time.sleep(1)

print("\n--- Stap 3: robot_1 vraagt toegang tot een gang ---")
aisle_request("robot_1", aisle_id="aisle_1", task_id="task_1")
time.sleep(1)

print("\n--- Stap 4: robot_1 rondt taak af ---")
task_status("robot_1", task_id="task_1", status="DONE")
time.sleep(1)

print("\n--- Stap 5: robot_2 weigert taak ---")
task_status("robot_2", task_id="task_2", status="REJECTED")
time.sleep(1)

print("\n--- Stap 6: finale heartbeat van alle robots ---")
heartbeat("robot_1", x=0.0, y=0.0, theta=0.0)
heartbeat("robot_2", x=1.0, y=0.5, theta=0.5)
heartbeat("robot_3", x=2.5, y=1.5, theta=0.8)
time.sleep(0.5)

print("\nKlaar. Bekijk de serveroutput voor de registry updates.")

client.loop_stop()
client.disconnect()
