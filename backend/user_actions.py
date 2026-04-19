# backend/user_actions.py

import random
from backend.simulation import mutation_roll, MUTATION_TABLE
from backend.world_state import world_state


# --- Evolution point costs ---
COSTS = {
    "deploy_disease": 0,
    "virus_jump": 25,
    "force_mutation": 30,
}


def _check_evo_points(cost: float) -> bool:
    return world_state["evolution_points"] >= cost


def _deduct_evo_points(cost: float):
    world_state["evolution_points"] = max(world_state["evolution_points"] - cost, 0.0)


# ---  Evolution Actions ---


def deploy_disease(target: str, value=None) -> dict:
    """
    Seed initial infection in a country.
    Free action -- no evolution point cost.
    Can only be used once per game via /deploy endpoint.
    This is kept here for SocketIO user_action compatibility.
    """
    if not world_state["simulation_running"]:
        return {
            "status": "failed",
            "message": "Simulation not started yet. Use /deploy endpoint first.",
        }

    if target not in world_state["countries"]:
        return {"status": "failed", "message": f"Unknown country: {target}"}

    country = world_state["countries"][target]

    if country["infected"] > 0.10:
        return {"status": "failed", "message": f"{target} is already heavily infected."}

    # Boost existing infection rather than reset it
    country["infected"] = min(country["infected"] + 0.05, 1.0)
    world_state["last_user_action"] = f"boosted infection in {target}"

    return {
        "status": "success",
        "message": f"Infection boosted in {target}.",
    }


def virus_jump(target: str, value=None) -> dict:
    """
    Jump virus to a new country, seeding 3% infection.
    Costs 25 evolution points.
    Most useful for jumping to uninfected countries far from current spread.
    """
    if not world_state["simulation_running"]:
        return {"status": "failed", "message": "Simulation not running."}

    cost = COSTS["virus_jump"]
    if not _check_evo_points(cost):
        return {
            "status": "failed",
            "message": f"Not enough evolution points. Need {cost}, have {world_state['evolution_points']:.1f}.",
        }

    if target not in world_state["countries"]:
        return {
            "status": "failed",
            "message": f"Unknown country: {target}. Valid: {list(world_state['countries'].keys())}",
        }

    country = world_state["countries"][target]

    if country["infected"] > 0.05:
        return {
            "status": "failed",
            "message": f"{target} already has significant infection ({country['infected'] * 100:.1f}%). Jump wasted.",
        }

    # Bypass airport/border closures -- this is a direct biological jump
    country["infected"] = min(country["infected"] + 0.03, 1.0)
    _deduct_evo_points(cost)
    world_state["last_user_action"] = f"virus jumped to {target}"

    return {
        "status": "success",
        "message": f"Virus jumped to {target}. 3% infection seeded. ({cost} evo pts spent)",
        "evo_remaining": round(world_state["evolution_points"], 1),
    }


def force_mutation(target: str, value=None) -> dict:
    """
    Force an immediate mutation roll at 2x base probability.
    Costs 30 evolution points.
    target parameter is unused -- mutations are global.
    """
    if not world_state["simulation_running"]:
        return {"status": "failed", "message": "Simulation not running."}

    cost = COSTS["force_mutation"]
    if not _check_evo_points(cost):
        return {
            "status": "failed",
            "message": f"Not enough evolution points. Need {cost}, have {world_state['evolution_points']:.1f}.",
        }

    active = world_state["active_mutations"]

    if len(active) >= 3:
        return {
            "status": "failed",
            "message": "Maximum mutations (3) already active. Cannot mutate further.",
        }

    # Get available mutations not yet active
    available = [
        (name, chance) for name, chance in MUTATION_TABLE if name not in active
    ]

    if not available:
        return {"status": "failed", "message": "No mutations available to trigger."}

    # Calculate boosted mutation chance
    global_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    ) / sum(c["population"] for c in world_state["countries"].values())

    time_factor = 1 + (world_state["tick"] / 365) * 0.5
    base_chance = global_infected * time_factor

    triggered = None
    for mutation_name, mutation_base in available:
        # 2x probability boost from forced mutation
        if random.random() < (mutation_base * base_chance * 2.0):
            triggered = mutation_name
            break

    # If no mutation rolled naturally, force the cheapest available one
    if not triggered:
        triggered = available[0][0]

    active.append(triggered)
    _deduct_evo_points(cost)
    world_state["last_user_action"] = f"forced mutation: {triggered}"

    return {
        "status": "success",
        "message": f"Mutation triggered: {triggered}. ({cost} evo pts spent)",
        "mutation": triggered,
        "active_mutations": active,
        "evo_remaining": round(world_state["evolution_points"], 1),
    }


# --- Dispacter ---

USER_ACTION_MAP = {
    "deploy_disease": deploy_disease,
    "virus_jump": virus_jump,
    "force_mutation": force_mutation,
}


def dispatch_user_action(action_type: str, target: str, value=None) -> dict:
    if action_type not in USER_ACTION_MAP:
        return {"status": "failed", "message": f"Unknown user action: {action_type}"}

    try:
        return USER_ACTION_MAP[action_type](target, value)
    except Exception as e:
        return {
            "status": "failed",
            "message": f"User action {action_type} crashed: {str(e)}",
        }
