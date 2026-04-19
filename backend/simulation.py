# fullyhacks/backend/simulation.py
"""
fullyhacks/backend/simulation.py

Determines virus spread give the following variables:
1) Airport status (route specific)
2) Port status (route specific)
3) Land border status (neighbor specific)
4) Population Nutrition Status
5) Containment Status (reduces spread speed)

Determines Mutation given:
1) Time (rolls for random mutation once 7 ticks)
"""

import random
from world_state import AIRPORTS, AIRPORT_ROUTES, PORTS, PORT_ROUTES

# Base rates
BASE_TRANSMISSION = 0.03
BASE_MORTALITY = 0.002
MUTATION_INTERVAL = 7  # ticks


def get_airport_modifier(country_name, world_state):
    """Calculate total transmission boost from open airport routes to infected countries."""
    modifier = 0.0
    airport_status = world_state["airport_status"]
    countries = world_state["countries"]

    for airport_code, airport_data in AIRPORTS.items():
        if airport_data["country"] != country_name:
            continue
        if not airport_status.get(airport_code, True):
            continue

        for a, b in AIRPORT_ROUTES:
            other_airport = None
            if a == airport_code:
                other_airport = b
            elif b == airport_code:
                other_airport = a

            if other_airport and other_airport in AIRPORTS:
                other_country = AIRPORTS[other_airport]["country"]
                if countries[other_country]["infected"] > 0.01:
                    traffic = AIRPORTS[other_airport]["traffic"]
                    modifier += 0.30 * traffic

    return modifier


def get_port_modifier(country_name, world_state):
    """Calculate total transmission boost from open port routes to infected countries."""
    modifier = 0.0
    port_status = world_state["port_status"]
    countries = world_state["countries"]

    for port_code, port_data in PORTS.items():
        if port_data["country"] != country_name:
            continue
        if not port_status.get(port_code, True):
            continue

        for a, b in PORT_ROUTES:
            other_port = None
            if a == port_code:
                other_port = b
            elif b == port_code:
                other_port = a

            if other_port and other_port in PORTS:
                other_country = PORTS[other_port]["country"]
                if countries[other_country]["infected"] > 0.01:
                    traffic = PORTS[other_port]["traffic"]
                    modifier += 0.15 * traffic

    return modifier


def get_transmission_modifier(country_name, world_state):
    """Calculate total transmission boost from open borders to infected countries."""
    countries = world_state["countries"]
    country = countries[country_name]
    modifier = 0.0

    # Airport routes
    airport_mod = get_airport_modifier(country_name, world_state)
    modifier += airport_mod

    # Port routes
    port_mod = get_port_modifier(country_name, world_state)
    modifier += port_mod

    # Land borders
    for neighbor, is_open in country["land_borders"].items():
        if is_open and countries[neighbor]["infected"] > 0.01:
            modifier += 0.10

    return modifier


def calculate_spread(country_name, world_state):
    """SIR-based spread for one country per tick."""
    country = world_state["countries"][country_name]
    mutations = world_state["active_mutations"]

    infected = country["infected"]
    susceptible = 1.0 - infected - (country["dead"] / max(country["population"], 1))
    susceptible = max(susceptible, 0.0)

    # Base transmission modified by mutations
    transmission = BASE_TRANSMISSION
    if "airborne" in mutations:
        transmission *= 1.5
    if "faster_incubation" in mutations:
        transmission *= 2.0

    # Border modifiers
    border_modifier = get_transmission_modifier(country_name, world_state)
    effective_transmission = transmission * (1 + border_modifier)

    # Containment reduces spread
    effective_transmission *= 1.0 - country["containment_level"]

    # Malnourished population spreads faster
    if country["food_water_supply"] < 0.3:
        effective_transmission *= 1.20

    # SIR delta: new infections this tick
    new_infected = effective_transmission * susceptible * infected
    country["infected"] = min(infected + new_infected, 1.0)


def calculate_deaths(country_name, world_state):
    """Calculate deaths this tick and reduce population + GDP."""
    country = world_state["countries"][country_name]
    mutations = world_state["active_mutations"]

    mortality = BASE_MORTALITY
    if "increased_lethality" in mutations:
        mortality += 0.005

    # Vaccine reduces mortality
    vaccine_effect = world_state["global_vaccine_progress"] * 0.8
    effective_mortality = mortality * (1.0 - vaccine_effect)

    new_deaths = int(country["population"] * country["infected"] * effective_mortality)
    country["dead"] += new_deaths
    country["population"] = max(country["population"] - new_deaths, 0)

    # GDP decays with death toll and lockdowns
    death_ratio = country["dead"] / max(country["population"], 1)
    country["gdp"] = max(country["gdp"] - (death_ratio * 0.01), 0.0)


def mutation_roll(world_state):
    """Stochastic mutation check. Runs every MUTATION_INTERVAL ticks."""
    mutations = world_state["active_mutations"]
    if len(mutations) >= 3:
        return  # Max mutations reached

    global_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    ) / sum(c["population"] for c in world_state["countries"].values())

    time_factor = 1 + (world_state["tick"] / 365) * 0.5
    mutation_chance = global_infected * time_factor

    mutation_table = [
        ("airborne", 0.15),
        ("drug_resistance", 0.20),
        ("increased_lethality", 0.10),
        ("symptom_suppression", 0.25),
        ("faster_incubation", 0.20),
    ]

    for mutation_name, base_chance in mutation_table:
        if mutation_name not in mutations:
            if random.random() < base_chance * mutation_chance:
                mutations.append(mutation_name)
                print(
                    f"[MUTATION] {mutation_name} triggered at tick {world_state['tick']}"
                )
                break  # One mutation per roll


def apply_spread_tick(world_state):
    """Main tick function. Call this every second from the tick loop."""
    world_state["tick"] += 1

    # get current spread & deaths
    for country_name in world_state["countries"]:
        calculate_spread(country_name, world_state)
        calculate_deaths(country_name, world_state)

    # update global vaccine progress
    total_research = sum(
        c["research_capacity"] * c["gdp"] for c in world_state["countries"].values()
    )

    vaccine_delta = total_research * 0.0005
    world_state["global_vaccine_progress"] = min(
        world_state["global_vaccine_progress"] + vaccine_delta, 1.0
    )

    # Mutation check every 7 ticks
    if world_state["tick"] % MUTATION_INTERVAL == 0:
        mutation_roll(world_state)

    # Evolution points accumulate for user
    global_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    ) / sum(c["population"] for c in world_state["countries"].values())

    world_state["evolution_points"] += global_infected * 10

