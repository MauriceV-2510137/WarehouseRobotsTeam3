import time
import json
import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_message(client, userdata, msg):
    print("SERVER RECEIVED:", msg.topic, msg.payload.decode())
client.on_message = on_message

client.connect("localhost")

client.loop_start()

client.subscribe("robot/default/heartbeat")

time.sleep(10)

# Send task
print("SERVER SENDING: t1, shelf: [2.0, 1.0], base: [0.0, 0.0]")
client.publish(
    "robot/default/task/assign",
    json.dumps({
        "task_id": "t1",
        "shelf": [2.0, 1.0],
        "base": [0.0, 0.0]
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