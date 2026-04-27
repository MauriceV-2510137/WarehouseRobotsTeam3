from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.routes import robots
from server.core.server import Server

def create_app(server: Server) -> FastAPI:
    app = FastAPI(title="Warehouse Robot API", version="1.0.0")
    app.state.server = server

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(robots.router, prefix="/api")

    return app