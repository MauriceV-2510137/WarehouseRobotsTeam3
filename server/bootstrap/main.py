from server.infrastructure.mqtt.mqtt_server_client import MqttServerClient
from server.core.server import Server
import time

def run():
    comm = MqttServerClient()
    server = Server(comm)

    comm.connect()

    dt = 0.1
    try:
        while server._running:
            server.update(dt)
            time.sleep(dt)

    except KeyboardInterrupt:
        print("Shutting down server...")

    finally:
        comm.disconnect()