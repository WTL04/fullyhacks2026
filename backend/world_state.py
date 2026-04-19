# backend/world_state.py
import random

world_state = {
    "tick": 0,
    "game_status": None,
    "simulation_running": False,
    "simulation_paused": False,
    "speed_multiplier": 1,
    "last_user_action": None,
    "last_action_results": [],
    "active_mutations": [],
    "evolution_points": 50,
    "global_vaccine_progress": 0.0,
    "research_boosts": {},  # {"Brazil": {"multiplier": 1.5, "ticks_remaining": 10}}
    "shared_data_pairs": [],  # ["USA-Brazil", "Canada-USA"]
    "drug_resistance_counter": None,  # None or {"ticks_remaining": 14}
    "countries": {
        "USA": {
            "population": 335000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 1.0,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 3,
            "land_borders": {"Canada": True, "Mexico": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Canada": {
            "population": 38000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.75,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 2,
            "land_borders": {"USA": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Mexico": {
            "population": 130000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.55,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 1,
            "land_borders": {"USA": True, "Colombia": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Brazil": {
            "population": 215000000,
            "infected": 0.15,  # TEST: Adding infection to debug frontend
            "dead": 0,
            "gdp": 0.60,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 2,
            "land_borders": {"Colombia": True, "Argentina": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Colombia": {
            "population": 52000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.45,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 1,
            "land_borders": {"Mexico": True, "Venezuela": True, "Brazil": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Venezuela": {
            "population": 28000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.35,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 0.7,
            "research_capacity": 0,
            "land_borders": {"Colombia": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Argentina": {
            "population": 46000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.50,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 1,
            "land_borders": {"Brazil": True, "Chile": True},
            "airports_open": True,
            "ports_open": True,
        },
        "Chile": {
            "population": 19000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.65,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 1,
            "land_borders": {"Argentina": True},
            "airports_open": True,
            "ports_open": True,
        },
    },
}


def get_global_infected():
    total_pop = sum(c["population"] for c in world_state["countries"].values())
    total_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    )
    return total_infected / total_pop if total_pop > 0 else 0.0


def get_utility_score():
    w1, w2, w3 = 0.5, 0.3, 0.2
    total_pop = sum(c["population"] for c in world_state["countries"].values())
    death_penalty = (
        sum(c["dead"] for c in world_state["countries"].values()) / total_pop
    )
    research_bonus = world_state["global_vaccine_progress"]
    gdp_bonus = sum(c["gdp"] for c in world_state["countries"].values()) / len(
        world_state["countries"]
    )
    return round(-(w1 * death_penalty) + (w2 * research_bonus) + (w3 * gdp_bonus), 4)


def check_win_condition():
    global_infected = get_global_infected()
    gdp_values = [c["gdp"] for c in world_state["countries"].values()]

    if global_infected >= 0.60:
        return "user_wins"
    if world_state["global_vaccine_progress"] >= 1.0 and global_infected < 0.05:
        return "ai_wins"
    if sum(gdp_values) / len(gdp_values) < 0.05:
        return "collapse"
    return None


def initialize_simulation():
    """Initializes the simulation state. Patient Zero is now determined by the user."""
    world_state["simulation_running"] = False
    world_state["simulation_paused"] = False
    world_state["tick"] = 0
    world_state["game_status"] = None
    world_state["active_mutations"] = []
    world_state["evolution_points"] = 50
    world_state["global_vaccine_progress"] = 0.0
    world_state["last_user_action"] = None
    world_state["last_action_results"] = []
    world_state["research_boosts"] = {}
    world_state["shared_data_pairs"] = []
    world_state["drug_resistance_counter"] = None
    # Reset all countries to starting values
    for name, country in world_state["countries"].items():
        country["infected"] = 0.0
        country["dead"] = 0
        country["containment_level"] = 0.0
        country["airports_open"] = True
        country["ports_open"] = True
        country["land_borders"] = {k: True for k in country["land_borders"]}
    print("Simulation initialized: Waiting for user to deploy the virus.")


def reset_world_state():
    import importlib
    import world_state as ws

    importlib.reload(ws)
