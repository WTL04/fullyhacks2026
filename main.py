import asyncio
import socketio
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from backend.coordinator import run_coordinator
from backend.actions import dispatch_directives
from backend.world_state import world_state, check_win_condition, initialize_simulation
from backend.simulation import apply_spread_tick

# --- Config ---
COORDINATOR_INTERVAL = 5  # run coordinator every N ticks


# --- Background Tasks ---
async def health_broadcast():
    """Broadcast health status every 5 seconds."""
    while True:
        await sio.emit("health", {"status": "ok", "tick": "server alive"})
        await asyncio.sleep(5)


async def tick_loop():
    """Main simulation loop - runs every tick."""
    while world_state.get("game_status") is None:
        # Wait for user to deploy virus before starting
        if not world_state["simulation_running"]:
            await asyncio.sleep(0.5)
            continue

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
                "evolution_points": world_state["evolution_points"],
                "global_infected": sum(
                    c["population"] * c["infected"]
                    for c in world_state["countries"].values()
                )
                / sum(c["population"] for c in world_state["countries"].values()),
                "utility_score": _get_utility(),
            },
        )

        # Run coordinator every N ticks
        if world_state["tick"] % COORDINATOR_INTERVAL == 0:
            thought, actions = await run_coordinator(world_state, sio)
            results = dispatch_directives(actions)
            world_state["last_action_results"] = results
            await sio.emit("action_results", results)
            print(f"\n[TICK {world_state['tick']}] Coordinator Thought: {thought}")
            print(
                f"[TICK {world_state['tick']}] Actions: {json.dumps(actions, indent=2)}"
            )
            print(
                f"[TICK {world_state['tick']}] Dispatched {len(actions)} actions, "
                f"{len([r for r in results if r.get('status') == 'failed'])} failed"
            )

        # Check win/lose condition
        result = check_win_condition()
        if result:
            world_state["game_status"] = result
            await sio.emit("game_over", {"result": result})
            break

        await asyncio.sleep(1)


def _get_utility():
    """Calculate utility score for state broadcast."""
    try:
        from backend.world_state import get_utility_score

        return get_utility_score()
    except Exception:
        return 0.0


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_simulation()
    print("Simulation initialized: Waiting for user to deploy the virus.")
    asyncio.create_task(health_broadcast())
    asyncio.create_task(tick_loop())
    print("Simulation started")
    yield
    print("Application is shutting down")


# --- Server Setup ---
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI(title="fullyhacks", lifespan=lifespan)
socket_app = socketio.ASGIApp(sio, app)


def _get_full_state():
    """Return the complete state dictionary for frontend updates."""
    global_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    ) / sum(c["population"] for c in world_state["countries"].values())
    return {
        "tick": world_state["tick"],
        "countries": world_state["countries"],
        "global_vaccine_progress": world_state["global_vaccine_progress"],
        "active_mutations": world_state["active_mutations"],
        "evolution_points": world_state["evolution_points"],
        "global_infected": global_infected,
        "utility_score": _get_utility(),
    }


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    # Send current state immediately if simulation is already running
    if world_state["simulation_running"]:
        await sio.emit("state_update", _get_full_state(), to=sid)


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


@sio.event
async def user_action(sid, data):
    """Handle user actions from the frontend."""
    action_type = data.get("type")
    target = data.get("target")
    value = data.get("value")
    from backend.user_actions import dispatch_user_action

    result = dispatch_user_action(action_type, target, value)
    await sio.emit("action_results", [result])
    print(f"User Action: {action_type} on {target} -> {result['status']}")


# --- HTTP Endpoints ---
class DeployAction(BaseModel):
    country: str


@app.post("/deploy")
async def deploy_virus(action: DeployAction):
    country = action.country.strip()
    countries = world_state["countries"]

    if country not in countries:
        return JSONResponse(
            status_code=400,
            content={
                "status": "failed",
                "message": f"Unknown country: {country}. Valid options: {list(countries.keys())}",
            },
        )

    if world_state["simulation_running"]:
        return JSONResponse(
            status_code=400,
            content={"status": "failed", "message": "Simulation already running"},
        )

    # Seed the infection
    countries[country]["infected"] = 0.05
    world_state["last_user_action"] = f"deployed virus in {country}"
    world_state["simulation_running"] = True

    print(f"Virus deployed in {country} -- simulation starting")

    # Notify all connected clients
    await sio.emit("simulation_started", {"country": country})

    return {"status": "success", "message": f"Virus deployed in {country}"}


@app.post("/reset")
async def reset_simulation():
    initialize_simulation()
    await sio.emit("simulation_reset", {})
    print("Simulation reset")
    return {"status": "success"}


@app.post("/speed")
async def set_speed(data: dict):
    world_state["speed_multiplier"] = data.get("multiplier", 1)
    return {"status": "success"}


@app.get("/ping")
async def ping():
    return {"status": "ok", "tick": world_state["tick"]}


# --- Static Frontend ---
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
