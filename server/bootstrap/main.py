import asyncio
import sys
import socket
import uvicorn

from server.api.app import create_app
from server.core.server import Server
from server.infrastructure.mqtt.mqtt_server_client import MqttServerClient

_UPDATE_INTERVAL = 0.1

_TEST_TASKS = [
    (5, 3),  # aisle 5, shelf 3
    (3, 1),  # aisle 3, shelf 1
    (1, 2),  # aisle 1, shelf 2
]
_TEST_TASK_INTERVAL = 5.0   # seconds between each submission
_TEST_STARTUP_DELAY = 5.0   # wait for robots to come online first
 
async def _submit_test_tasks(server: Server) -> None:
    await asyncio.sleep(_TEST_STARTUP_DELAY)
 
    for aisle, shelf in _TEST_TASKS:
        record = server.task_dispatcher.submit(aisle, shelf)
        print(f"[TEST] Submitted task {record.task_id} → aisle {aisle}, shelf {shelf}")
        await asyncio.sleep(_TEST_TASK_INTERVAL)

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
            while server._running:
                server.update(_UPDATE_INTERVAL)
                await asyncio.sleep(_UPDATE_INTERVAL)
        finally:
            comm.disconnect()
 
    try:
        await asyncio.gather(
            uvi_server.serve(),
            server_loop(),
            _submit_test_tasks(server),
        )
    except asyncio.CancelledError:
        pass