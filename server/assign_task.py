"""
Assign a task to the robot running in the Webots simulator.

Usage (vanuit projectroot):
    python -m server.assign_task

Vereisten:
    1. mosquitto draait  -> & "C:\\Program Files\\mosquitto\\mosquitto.exe"
    2. server draait     -> python -m server.app
    3. Webots simulator draait met robot_controller

Warehouse layout (bovenaanzicht):
    y=+4 | corridor (north)
    y=+3 | [aisle_left_2]
    y=+2 | corridor
    y=+1 | [aisle_left]
    y= 0 | corridor (center)
    y=-1 | [aisle_right]
    y=-2 | corridor
    y=-3 | [aisle_right_2]
    y=-4 | corridor (south)

    Robot start: (0, 0)    Aisles beginnen bij x=4
"""
import json
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
ROBOT_ID = "default"

# Beschikbare corridors (aisle entry x=3, segment diep in aisle x=6.5)
AISLES = {
    "south":        {"aisle_pos": [3.0, -4.0], "segment_pos": [6.5, -4.0]},
    "center_south": {"aisle_pos": [3.0, -2.0], "segment_pos": [6.5, -2.0]},
    "center":       {"aisle_pos": [3.0,  0.0], "segment_pos": [6.5,  0.0]},
    "center_north": {"aisle_pos": [3.0,  2.0], "segment_pos": [6.5,  2.0]},
    "north":        {"aisle_pos": [3.0,  4.0], "segment_pos": [6.5,  4.0]},
}

def assign_task(aisle_name: str = "center_south", task_id: str = "task_1"):
    aisle = AISLES[aisle_name]

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    received_response = []

    def on_message(client, userdata, msg):
        data = json.loads(msg.payload.decode())
        print(f"\n[RESPONSE] {msg.topic}: {data}")
        received_response.append(data)

    client.on_message = on_message
    client.connect(BROKER)
    client.loop_start()
    client.subscribe(f"robot/{ROBOT_ID}/task/status")

    time.sleep(0.5)

    payload = {
        "task_id": task_id,
        "aisle_id": aisle_name,
        "aisle_pos": aisle["aisle_pos"],
        "segment_pos": aisle["segment_pos"],
        "base_pos": [0.0, 0.0],
    }

    print(f"Taak versturen naar robot '{ROBOT_ID}':")
    print(f"  aisle:       {aisle_name}")
    print(f"  aisle_pos:   {aisle['aisle_pos']}")
    print(f"  segment_pos: {aisle['segment_pos']}")
    print(f"  base_pos:    [0.0, 0.0]")

    client.publish(f"robot/{ROBOT_ID}/task/assign", json.dumps(payload))
    print("\nWacht op statusupdates van de robot (Ctrl+C om te stoppen)...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    import sys

    aisle = sys.argv[1] if len(sys.argv) > 1 else "center_south"
    task  = sys.argv[2] if len(sys.argv) > 2 else "task_1"

    if aisle not in AISLES:
        print(f"Onbekende aisle '{aisle}'. Kies uit: {list(AISLES.keys())}")
        sys.exit(1)

    assign_task(aisle, task)
