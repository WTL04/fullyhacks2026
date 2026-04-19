import socketio
import asyncio
from fastapi import FastAPI

# async server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# fastapi server
app = FastAPI(title="fullyhacks")

# wrapping fastapi with socketio asgi application
socket_app = socketio.ASGIApp(sio, app)


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


async def health_broadcast():
    while True:
        await sio.emit("health", {"status": "ok", "tick": "server alive"})
        await asyncio.sleep(5)


@app.on_event("startup")
async def startup():
    asyncio.create_task(health_broadcast())
