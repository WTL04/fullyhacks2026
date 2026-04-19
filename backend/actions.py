# backend/actions.py

from backend.world_state import world_state
from backend.simulation import AIRPORTS, PORTS

# ── GDP costs ──────────────────────────────────────────────────────────────────
COSTS = {
    "set_containment": 0.10,  # per 10-point containment increase
    "close_border": 0.03,
    "open_border": 0.00,  # free to reopen
    "close_airport": 0.08,  # scaled by traffic below
    "close_port": 0.05,  # scaled by traffic below
}


# ── Result helpers ─────────────────────────────────────────────────────────────
def _ok(message: str):
    return {"status": "success", "message": message}


def _fail(message: str):
    return {"status": "failed", "message": message}


# ── Individual actions ─────────────────────────────────────────────────────────


def set_containment(target: str, value: int) -> dict:
    """
    Set containment level for a country.
    value = 0-100 (integer), stored as 0.0-1.0 internally.
    Cost scales with how much containment is being added.
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown country: {target}")

    if not isinstance(value, (int, float)) or not (0 <= value <= 100):
        return _fail(f"value must be 0-100, got: {value}")

    country = countries[target]
    new_level = round(value / 100, 2)
    delta = max(new_level - country["containment_level"], 0)

    # Cost proportional to how much containment is being added
    gdp_cost = COSTS["set_containment"] * (delta * 10)

    if country["gdp"] < gdp_cost:
        return _fail(
            f"{target} cannot afford containment upgrade (needs {gdp_cost:.2f} GDP, has {country['gdp']:.2f})"
        )

    country["containment_level"] = new_level
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)

    # High containment also strains food supply
    if new_level > 0.6:
        country["food_water_supply"] = max(
            country["food_water_supply"] - (delta * 0.15), 0.0
        )

    return _ok(f"{target} containment set to {value}% (GDP -{gdp_cost:.2f})")


def close_border(target: str, value: str) -> dict:
    """
    Close land border between target country and value country.
    target = country closing the border (pays the cost)
    value  = neighbor country being blocked
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown country: {target}")
    if value not in countries:
        return _fail(f"Unknown neighbor: {value}")

    country = countries[target]

    if value not in country["land_borders"]:
        return _fail(f"{target} has no land border with {value}")
    if not country["land_borders"][value]:
        return _fail(f"Border {target}-{value} is already closed")

    gdp_cost = COSTS["close_border"]
    if country["gdp"] < gdp_cost:
        return _fail(f"{target} cannot afford border closure (needs {gdp_cost:.2f})")

    country["land_borders"][value] = False
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)
    country["food_water_supply"] = max(country["food_water_supply"] - 0.05, 0.0)

    return _ok(f"Border {target}-{value} closed (GDP -{gdp_cost})")


def open_border(target: str, value: str) -> dict:
    """
    Reopen a previously closed land border. Free action.
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown country: {target}")
    if value not in countries:
        return _fail(f"Unknown neighbor: {value}")

    country = countries[target]

    if value not in country["land_borders"]:
        return _fail(f"{target} has no land border with {value}")
    if country["land_borders"][value]:
        return _fail(f"Border {target}-{value} is already open")

    country["land_borders"][value] = True
    # Reopening border partially restores food supply
    country["food_water_supply"] = min(country["food_water_supply"] + 0.03, 1.0)

    return _ok(f"Border {target}-{value} reopened")


def close_airport(target: str, value=None) -> dict:
    """
    Close a specific airport by code.
    target = airport code (e.g. "JFK")
    value  = unused, kept for schema consistency
    """
    if target not in AIRPORTS:
        return _fail(f"Unknown airport code: {target}")

    if not world_state["airport_status"].get(target, True):
        return _fail(f"Airport {target} is already closed")

    airport = AIRPORTS[target]
    country_name = airport["country"]
    country = world_state["countries"][country_name]

    gdp_cost = round(COSTS["close_airport"] * airport["traffic"], 4)
    if country["gdp"] < gdp_cost:
        return _fail(
            f"{country_name} cannot afford closing {target} (needs {gdp_cost:.2f})"
        )

    world_state["airport_status"][target] = False
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)
    country["food_water_supply"] = max(
        country["food_water_supply"] - (0.10 * airport["traffic"]), 0.0
    )

    return _ok(f"Airport {target} ({country_name}) closed (GDP -{gdp_cost})")


def close_port(target: str, value=None) -> dict:
    """
    Close a specific port by code.
    target = port code (e.g. "PORT_NY")
    value  = unused, kept for schema consistency
    """
    if target not in PORTS:
        return _fail(f"Unknown port code: {target}")

    if not world_state["port_status"].get(target, True):
        return _fail(f"Port {target} is already closed")

    port = PORTS[target]
    country_name = port["country"]
    country = world_state["countries"][country_name]

    gdp_cost = round(COSTS["close_port"] * port["traffic"], 4)
    if country["gdp"] < gdp_cost:
        return _fail(
            f"{country_name} cannot afford closing {target} (needs {gdp_cost:.2f})"
        )

    world_state["port_status"][target] = False
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)
    # Ports carry cargo so food penalty is higher than airports
    country["food_water_supply"] = max(
        country["food_water_supply"] - (0.15 * port["traffic"]), 0.0
    )

    return _ok(f"Port {target} ({country_name}) closed (GDP -{gdp_cost})")


# ── Dispatcher ─────────────────────────────────────────────────────────────────

ACTION_MAP = {
    "set_containment": set_containment,
    "close_border": close_border,
    "open_border": open_border,
    "close_airport": close_airport,
    "close_port": close_port,
}


def dispatch_directives(actions: list) -> list:
    """
    Takes the parsed actions list from coordinator.py and executes each one.
    Returns a list of results for logging and coordinator feedback.

    Example input:
    [
        {"type": "close_airport", "target": "JFK", "value": null},
        {"type": "set_containment", "target": "Brazil", "value": 80}
    ]
    """
    results = []

    for action in actions:
        action_type = action.get("type")
        target = action.get("target")
        value = action.get("value")

        if action_type not in ACTION_MAP:
            results.append(_fail(f"Unknown action type: {action_type}"))
            continue

        try:
            result = ACTION_MAP[action_type](target, value)
        except Exception as e:
            result = _fail(f"Action {action_type} crashed: {str(e)}")

        results.append({**result, "action": action_type, "target": target})

    return results
