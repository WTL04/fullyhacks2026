import asyncio
import socketio
import json
from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.coordinator import run_coordinator
from backend.actions import dispatch_directives
from backend.world_state import world_state, check_win_condition, initialize_simulation
from backend.simulation import apply_spread_tick

# --- Config ---
COORDINATOR_INTERVAL = 10  # run coordinator every N ticks


# --- Background Tasks ---
async def health_broadcast():
    """Broadcast health status every 5 seconds."""
    while True:
        await sio.emit("health", {"status": "ok", "tick": "server alive"})
        await asyncio.sleep(5)


async def tick_loop():
    """Main simulation loop - runs every tick."""
    while world_state.get("game_status") is None:
        # Advance simulation
        apply_spread_tick(world_state)

        # Broadcast state to frontend
        await sio.emit(
            "state_update",
            {
                "tick": world_state["tick"],
                "countries": world_state["countries"],
                "global_vaccine_progress": world_state["global_vaccine_progress"],
                "active_mutations": world_state["active_mutations"],
            },
        )

        # Run coordinator every N ticks
        if world_state["tick"] % COORDINATOR_INTERVAL == 0:
            thought, actions = await run_coordinator(world_state, sio)

            # Dispatch actions and get results
            results = dispatch_directives(actions)

            # Store results for next cycle feedback
            world_state["last_action_results"] = results

            # Emit results to frontend
            await sio.emit("action_results", results)

            print(f"\n[TICK {world_state['tick']}] Coordinator Thought: {thought}")
            print(
                f"[TICK {world_state['tick']}] Actions: {json.dumps(actions, indent=2)}"
            )
            print(
                f"[TICK {world_state['tick']}] Dispatched {len(actions)} actions, {len([r for r in results if r.get('status') == 'failed'])} failed"
            )

        # Check win/lose condition
        result = check_win_condition()
        if result:
            world_state["game_status"] = result
            await sio.emit("game_over", {"result": result})
            break

        await asyncio.sleep(1)


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    initialize_simulation()
    asyncio.create_task(health_broadcast())
    asyncio.create_task(tick_loop())
    print("Simulation started")

    yield

    # Shutdown
    print("Application is shutting down")


# --- Server Setup (after lifespan is defined) ---
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI(title="fullyhacks", lifespan=lifespan)
socket_app = socketio.ASGIApp(sio, app)


# --- Socket Events ---
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
