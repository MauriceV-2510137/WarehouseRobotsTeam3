import asyncio
import uvicorn

from server.api.app import create_app
from server.core.server import Server
from server.infrastructure.mqtt.mqtt_server_client import MqttServerClient

_UPDATE_INTERVAL = 0.1

async def run() -> None:

    comm = MqttServerClient()
    server = Server(comm)
    comm.connect()

    app = create_app(server)
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    uvi_server = uvicorn.Server(config)

    async def server_loop() -> None:
        try:
            while server._running:
                server.update(_UPDATE_INTERVAL)
                await asyncio.sleep(_UPDATE_INTERVAL)
        finally:
            comm.disconnect()
 
    try:
        await asyncio.gather(
            uvi_server.serve(),
            server_loop(),
        )
    except asyncio.CancelledError:
        pass