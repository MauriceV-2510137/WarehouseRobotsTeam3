import time
import json
import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_message(client, userdata, msg):
    print("SERVER RECEIVED:", msg.topic, msg.payload.decode())

    if msg.topic.startswith("aisle/") and msg.topic.endswith("/request"):
        payload = json.loads(msg.payload.decode())

        aisle_id = payload["aisle_id"]
        robot_id = payload["robot_id"]

        # respond after delay (non-blocking)
        def delayed_response():
            time.sleep(2)

            response = {
                "aisle_id": aisle_id,
                "granted": True
            }

            topic = f"robot/{robot_id}/aisle/response"

            print(f"SERVER SENDING GRANT → {topic}")
            client.publish(topic, json.dumps(response))

        import threading
        threading.Thread(target=delayed_response, daemon=True).start()

client.on_message = on_message

client.connect("localhost")

client.loop_start()

client.subscribe("robot/+/heartbeat")
client.subscribe("aisle/+/request")

time.sleep(5)

# Send task
print("SERVER SENDING: t1, segment: [6.5, -4.0], base: [0.0, 0.0]")
client.publish(
    "robot/robot_1/task/assign",
    json.dumps({
        "task_id": "t1",
        "aisle_id": "a1",
        "aisle_pos": [3, -4],
        "segment_pos": [6.5, -4],
        "base_pos": [0.0, 0.0]
    })
)

time.sleep(5)

print("SERVER SENDING: t2, segment: [4.5, 0.0], base: [0.0, 0.0]")
client.publish(
    "robot/robot_5/task/assign",
    json.dumps({
        "task_id": "t2",
        "aisle_id": "a1",
        "aisle_pos": [3, 0],
        "segment_pos": [4.5, 0],
        "base_pos": [0.0, 0.0]
    })
)

# Keep server alive
try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Shutting down server...")
    client.loop_stop()
    client.disconnect()