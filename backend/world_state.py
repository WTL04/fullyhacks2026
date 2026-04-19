# backend/world_state.py

AIRPORTS = {
    "JFK": {"country": "USA", "lat": 40.6413, "lon": -73.7781, "traffic": 0.9},
    "GRU": {"country": "Brazil", "lat": -23.4356, "lon": -46.4731, "traffic": 0.8},
    "BOG": {"country": "Colombia", "lat": 4.7016, "lon": -74.1469, "traffic": 0.6},
    "EZE": {"country": "Argentina", "lat": -34.8222, "lon": -58.5358, "traffic": 0.5},
    "SCL": {"country": "Chile", "lat": -33.3930, "lon": -70.7858, "traffic": 0.5},
    "CCS": {"country": "Venezuela", "lat": 10.6031, "lon": -66.9906, "traffic": 0.3},
    "MEX": {"country": "Mexico", "lat": 19.4363, "lon": -99.0721, "traffic": 0.7},
    "YYZ": {"country": "Canada", "lat": 43.6777, "lon": -79.6248, "traffic": 0.7},
}

AIRPORT_ROUTES = [
    ("JFK", "GRU"),
    ("JFK", "BOG"),
    ("JFK", "EZE"),
    ("JFK", "SCL"),
    ("JFK", "MEX"),
    ("JFK", "YYZ"),
    ("GRU", "BOG"),
    ("GRU", "EZE"),
    ("GRU", "SCL"),
    ("MEX", "BOG"),
    ("MEX", "GRU"),
]

PORTS = {
    "PORT_NY": {"country": "USA", "lat": 40.6892, "lon": -74.0445, "traffic": 0.9},
    "PORT_LA": {"country": "USA", "lat": 33.7395, "lon": -118.2620, "traffic": 0.8},
    "PORT_VAN": {"country": "Canada", "lat": 49.2827, "lon": -123.1207, "traffic": 0.6},
    "PORT_VER": {"country": "Mexico", "lat": 19.2000, "lon": -96.1333, "traffic": 0.6},
    "PORT_CTG": {
        "country": "Colombia",
        "lat": 10.3910,
        "lon": -75.4794,
        "traffic": 0.5,
    },
    "PORT_MAR": {
        "country": "Venezuela",
        "lat": 10.6500,
        "lon": -63.1800,
        "traffic": 0.3,
    },
    "PORT_SAN": {"country": "Brazil", "lat": -23.9619, "lon": -46.3042, "traffic": 0.8},
    "PORT_RIO": {"country": "Brazil", "lat": -22.8938, "lon": -43.1729, "traffic": 0.7},
    "PORT_BUE": {
        "country": "Argentina",
        "lat": -34.5997,
        "lon": -58.3819,
        "traffic": 0.6,
    },
    "PORT_VAL": {"country": "Chile", "lat": -33.0472, "lon": -71.6127, "traffic": 0.5},
}

PORT_ROUTES = [
    ("PORT_NY", "PORT_SAN"),
    ("PORT_NY", "PORT_RIO"),
    ("PORT_NY", "PORT_CTG"),
    ("PORT_NY", "PORT_BUE"),
    ("PORT_LA", "PORT_VAL"),
    ("PORT_LA", "PORT_SAN"),
    ("PORT_VAN", "PORT_SAN"),
    ("PORT_VAN", "PORT_VAL"),
    ("PORT_VER", "PORT_CTG"),
    ("PORT_VER", "PORT_SAN"),
    ("PORT_CTG", "PORT_MAR"),
    ("PORT_CTG", "PORT_SAN"),
    ("PORT_SAN", "PORT_BUE"),
    ("PORT_SAN", "PORT_VAL"),
    ("PORT_RIO", "PORT_BUE"),
    ("PORT_BUE", "PORT_VAL"),
]

world_state = {
    "tick": 0,
    "game_status": None,
    "active_mutations": [],
    "evolution_points": 0,
    "global_vaccine_progress": 0.0,
    "airport_status": {
        "JFK": True,
        "GRU": True,
        "BOG": True,
        "EZE": True,
        "SCL": True,
        "CCS": True,
        "MEX": True,
        "YYZ": True,
    },
    "port_status": {
        "PORT_NY": True,
        "PORT_LA": True,
        "PORT_VAN": True,
        "PORT_VER": True,
        "PORT_CTG": True,
        "PORT_MAR": True,
        "PORT_SAN": True,
        "PORT_RIO": True,
        "PORT_BUE": True,
        "PORT_VAL": True,
    },
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
        },
        "Brazil": {
            "population": 215000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.60,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 2,
            "land_borders": {"Colombia": True, "Argentina": True},
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
        },
        "Venezuela": {
            "population": 28000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.20,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 0.7,
            "research_capacity": 0,
            "land_borders": {"Colombia": True},
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
        },
        "Chile": {
            "population": 19000000,
            "infected": 0.0,
            "dead": 0,
            "gdp": 0.55,
            "containment_level": 0.0,
            "vaccine_progress": 0.0,
            "food_water_supply": 1.0,
            "research_capacity": 1,
            "land_borders": {"Argentina": True},
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


def reset_world_state():
    import importlib
    import world_state as ws

    importlib.reload(ws)

