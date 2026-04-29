import asyncio
import sys
import socket
import uvicorn

from server.api.app import create_app
from server.core.server import Server
from server.infrastructure.mqtt.mqtt_server_client import MqttServerClient

_UPDATE_INTERVAL = 0.1

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def run() -> None:
    port = 8000

    if is_port_in_use(port):
        print(f"[Server] Port {port} is already in use — is the server already running?")
        print("[Server] Shutting down...")
        sys.exit(0)  # exit code 0 = clean exit

    comm = MqttServerClient()
    server = Server(comm)
    comm.connect()

    app = create_app(server)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    uvi_server = uvicorn.Server(config)

    async def server_loop() -> None:
        try:
            while server.is_running():
                server.update(_UPDATE_INTERVAL)
                await asyncio.sleep(_UPDATE_INTERVAL)
        finally:
            comm.disconnect()
 
    try:
        await asyncio.gather(
            uvi_server.serve(),
            server_loop()
        )
    except asyncio.CancelledError:
        pass