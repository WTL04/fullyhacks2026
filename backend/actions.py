# backend/actions.py

from backend.world_state import world_state

# ── GDP costs ──────────────────────────────────────────────────────────────────
COSTS = {
    "set_containment": 0.05,  # per 10-point containment increase
    "close_border": 0.02,
    "open_border": 0.00,  # free to reopen
    "close_airport": 0.06,
    "close_port": 0.04,
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
    Close airports for a specific country.
    target = country name (e.g. "USA")
    """
    countries = world_state["countries"]
    if target not in countries:
        return _fail(f"Unknown country: {target}")

    country = countries[target]
    if not country.get("airports_open", True):
        return _fail(f"Airports in {target} are already closed")

    gdp_cost = COSTS["close_airport"]
    if country["gdp"] < gdp_cost:
        return _fail(f"{target} cannot afford closing airports (needs {gdp_cost:.2f})")

    country["airports_open"] = False
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)
    country["food_water_supply"] = max(country["food_water_supply"] - 0.1, 0.0)

    return _ok(f"Airports in {target} closed (GDP -{gdp_cost})")


def close_port(target: str, value=None) -> dict:
    """
    Close ports for a specific country.
    target = country name (e.g. "USA")
    """
    countries = world_state["countries"]
    if target not in countries:
        return _fail(f"Unknown country: {target}")

    country = countries[target]
    if not country.get("ports_open", True):
        return _fail(f"Ports in {target} are already closed")

    gdp_cost = COSTS["close_port"]
    if country["gdp"] < gdp_cost:
        return _fail(f"{target} cannot afford closing ports (needs {gdp_cost:.2f})")

    country["ports_open"] = False
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)
    country["food_water_supply"] = max(country["food_water_supply"] - 0.15, 0.0)

    return _ok(f"Ports in {target} closed (GDP -{gdp_cost})")


# ── Research actions ───────────────────────────────────────────────────────────


def fund_research(target: str, value=None) -> dict:
    """
    Boost research output for a country for 10 ticks.
    target = country name
    value  = multiplier as int (e.g. 2 = 2x research speed)
              defaults to 2 if not provided Cost: 10% GDP upfront. Country must have research_capacity > 0.
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown country: {target}")

    country = countries[target]

    if country["research_capacity"] == 0:
        return _fail(f"{target} has no research institutions to fund")

    # Default multiplier of 2x if not specified
    multiplier = float(value) if value is not None else 2.0
    multiplier = max(1.1, min(multiplier, 3.0))  # clamp between 1.1x and 3x

    gdp_cost = 0.10
    if country["gdp"] < gdp_cost:
        return _fail(
            f"{target} cannot afford research funding "
            f"(needs {gdp_cost:.2f} GDP, has {country['gdp']:.2f})"
        )

    # If boost already active, extend it rather than overwrite
    existing = world_state["research_boosts"].get(target)
    if existing:
        existing["ticks_remaining"] += 10
        existing["multiplier"] = max(existing["multiplier"], multiplier)
        country["gdp"] = round(country["gdp"] - gdp_cost, 4)
        return _ok(
            f"{target} research boost extended "
            f"({existing['ticks_remaining']} ticks remaining, "
            f"{existing['multiplier']}x multiplier, GDP -{gdp_cost})"
        )

    world_state["research_boosts"][target] = {
        "multiplier": multiplier,
        "ticks_remaining": 10,
    }
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)

    return _ok(
        f"{target} research funded at {multiplier}x for 10 ticks (GDP -{gdp_cost})"
    )


def share_data(target: str, value: str) -> dict:
    """
    One-time data sharing between two countries.
    target = country A
    value  = country B
    Both countries receive a flat +2% vaccine progress boost.
    One use per country pair per game.

    Cost: 5% GDP from the initiating country (target).
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown country: {target}")
    if not value or value not in countries:
        return _fail(f"Unknown partner country: {value}")
    if target == value:
        return _fail("Cannot share data with itself")

    # Check both countries have research capacity
    if countries[target]["research_capacity"] == 0:
        return _fail(f"{target} has no research institutions")
    if countries[value]["research_capacity"] == 0:
        return _fail(f"{value} has no research institutions to receive data")

    # Normalize pair key so USA-Brazil and Brazil-USA are the same
    pair_key = "-".join(sorted([target, value]))
    if pair_key in world_state["shared_data_pairs"]:
        return _fail(f"Data already shared between {target} and {value} this game")

    gdp_cost = 0.05
    if countries[target]["gdp"] < gdp_cost:
        return _fail(
            f"{target} cannot afford data sharing "
            f"(needs {gdp_cost:.2f}, has {countries[target]['gdp']:.2f})"
        )

    # Apply boost to both countries via vaccine progress
    boost = 0.02
    world_state["global_vaccine_progress"] = min(
        world_state["global_vaccine_progress"] + boost, 1.0
    )

    # Mark pair as used
    world_state["shared_data_pairs"].append(pair_key)
    countries[target]["gdp"] = round(countries[target]["gdp"] - gdp_cost, 4)

    return _ok(
        f"Data shared between {target} and {value}: "
        f"+{boost * 100:.0f}% global vaccine progress "
        f"(GDP -{gdp_cost}, pair locked for rest of game)"
    )


def develop_counter(target: str, value=None) -> dict:
    """
    Start development of a drug resistance counter.
    Only valid when drug_resistance mutation is active.
    Takes 14 ticks to complete.
    target = country funding the counter (must have research_capacity > 0)
    value  = unused

    Cost: 20% GDP from target country.
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown country: {target}")

    if "drug_resistance" not in world_state["active_mutations"]:
        return _fail("drug_resistance mutation is not active -- counter not needed")

    counter = world_state["drug_resistance_counter"]
    if counter is not None and counter["ticks_remaining"] > 0:
        return _fail(
            f"Counter already in development "
            f"({counter['ticks_remaining']} ticks remaining)"
        )
    if counter is not None and counter["ticks_remaining"] <= 0:
        return _fail("Counter already developed this game")

    country = countries[target]

    if country["research_capacity"] == 0:
        return _fail(f"{target} has no research institutions to develop counter")

    gdp_cost = 0.20
    if country["gdp"] < gdp_cost:
        return _fail(
            f"{target} cannot afford counter development "
            f"(needs {gdp_cost:.2f}, has {country['gdp']:.2f})"
        )

    world_state["drug_resistance_counter"] = {"ticks_remaining": 14}
    country["gdp"] = round(country["gdp"] - gdp_cost, 4)

    return _ok(
        f"Drug resistance counter started at {target} "
        f"(14 ticks to complete, GDP -{gdp_cost})"
    )


def foreign_aid(target: str, value: str) -> dict:
    """
    Transfer GDP from a donor country to a recipient country.
    target = donor country (pays the cost)
    value  = recipient country (receives the funds)

    Transfer amount: 15% of donor's current GDP.
    Donor must have GDP > 0.40 to afford aid without self-harm.
    Recipient GDP increases by 10% (5% lost to logistics overhead).
    """
    countries = world_state["countries"]

    if target not in countries:
        return _fail(f"Unknown donor country: {target}")
    if not value or value not in countries:
        return _fail(f"Unknown recipient country: {value}")
    if target == value:
        return _fail("Cannot send aid to itself")

    donor = countries[target]
    recipient = countries[value]

    if donor["gdp"] < 0.40:
        return _fail(
            f"{target} cannot afford foreign aid "
            f"(donor needs GDP > 0.40, has {donor['gdp']:.2f})"
        )

    transfer_cost = round(donor["gdp"] * 0.15, 4)
    recipient_gain = round(transfer_cost * 0.67, 4)  # 33% logistics loss

    donor["gdp"] = round(donor["gdp"] - transfer_cost, 4)
    recipient["gdp"] = min(round(recipient["gdp"] + recipient_gain, 4), 1.0)

    return _ok(
        f"{target} sent foreign aid to {value} "
        f"(donor GDP -{transfer_cost:.3f}, "
        f"recipient GDP +{recipient_gain:.3f})"
    )


def reduce_containment(target: str, value: int) -> dict:
    """
    Lower containment level to recover GDP.
    Accepts risk of increased spread in exchange for economic recovery.
    """
    countries = world_state["countries"]
    if target not in countries:
        return _fail(f"Unknown country: {target}")

    country = world_state["countries"][target]
    new_level = round(value / 100, 2)

    if new_level >= country["containment_level"]:
        return _fail(f"Use set_containment to increase, not reduce")

    old_level = country["containment_level"]
    country["containment_level"] = new_level

    # GDP partially recovers immediately when containment drops
    gdp_recovery = (old_level - new_level) * 0.05
    country["gdp"] = min(country["gdp"] + gdp_recovery, 1.0)

    return _ok(
        f"{target} containment reduced to {value}% "
        f"(GDP +{gdp_recovery:.3f}, spread risk increased)"
    )


# ── Dispatcher ─────────────────────────────────────────────────────────────────

ACTION_MAP = {
    "set_containment": set_containment,
    "close_border": close_border,
    "open_border": open_border,
    "close_airport": close_airport,
    "close_port": close_port,
    "fund_research": fund_research,
    "share_data": share_data,
    "develop_counter": develop_counter,
    "foreign_aid": foreign_aid,
    "reduce_containment": reduce_containment,
}


def dispatch_directives(actions: list) -> list:
    """
    Takes the parsed actions list from coordinator.py and executes each one.
    Returns a list of results for logging and coordinator feedback.

    Example input:
    [
        {"type": "close_airport", "target": "USA", "value": null},
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
