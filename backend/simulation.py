# fullyhacks/backend/simulation.py
"""
Determines virus spread give the following variables:
1) Airport status (country level)
2) Port status (country level)
3) Land border status (neighbor specific)
4) Population Nutrition Status
5) Containment Status (reduces spread speed)

Determines Mutation given:
1) Time (rolls for random mutation once 7 ticks)
"""

import random

# Base rates
BASE_TRANSMISSION = 0.01
BASE_MORTALITY = 0.001
MUTATION_INTERVAL = 10


def get_airport_modifier(country_name, world_state):
    """Calculate total transmission boost from open airports in infected countries."""
    modifier = 0.0
    countries = world_state["countries"]
    country = countries[country_name]

    if not country.get("airports_open", True):
        return 0.0

    for other_name, other in countries.items():
        if other_name != country_name and other["infected"] > 0.01:
            modifier += 0.30

    return modifier


def get_port_modifier(country_name, world_state):
    """Calculate total transmission boost from open ports in infected countries."""
    modifier = 0.0
    countries = world_state["countries"]
    country = countries[country_name]

    if not country.get("ports_open", True):
        return 0.0

    for other_name, other in countries.items():
        if other_name != country_name and other["infected"] > 0.01:
            modifier += 0.15

    return modifier


def get_transmission_modifier(country_name, world_state):
    """Calculate total transmission boost from open borders to infected countries."""
    countries = world_state["countries"]
    country = countries[country_name]
    modifier = 0.0

    # Airport modifiers
    modifier += get_airport_modifier(country_name, world_state)

    # Port modifiers
    modifier += get_port_modifier(country_name, world_state)

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

    # Vaccine reduces transmission as it progresses (immunity effect)
    vaccine_progress = world_state["global_vaccine_progress"]
    if vaccine_progress > 0:
        # Vaccine reduces transmission by up to 70% when fully deployed
        vaccine_transmission_reduction = vaccine_progress * 0.7
        effective_transmission *= 1.0 - vaccine_transmission_reduction

    # SIR delta: new infections this tick
    new_infected = effective_transmission * susceptible * infected
    country["infected"] = min(infected + new_infected, 1.0)

    # Vaccine also helps recover infected population (they become immune)
    if vaccine_progress > 0.3:  # Vaccine starts helping recovery after 30% progress
        recovery_rate = (
            vaccine_progress - 0.3
        ) * 0.02  # Up to 1.4% recovery per tick at 100%
        country["infected"] = max(country["infected"] - recovery_rate, 0.0)


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


MUTATION_TABLE = [
    ("airborne", 0.15),
    ("drug_resistance", 0.20),
    ("increased_lethality", 0.10),
    ("symptom_suppression", 0.25),
    ("faster_incubation", 0.20),
]


def mutation_roll(world_state):
    """Stochastic mutation check. Runs every MUTATION_INTERVAL ticks. Returns mutation name if triggered."""
    mutations = world_state["active_mutations"]
    if len(mutations) >= 3:
        return None  # Max mutations reached

    global_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    ) / sum(c["population"] for c in world_state["countries"].values())

    time_factor = 1 + (world_state["tick"] / 365) * 0.5
    mutation_chance = global_infected * time_factor

    for mutation_name, base_chance in MUTATION_TABLE:
        if mutation_name not in mutations:
            if random.random() < base_chance * mutation_chance:
                mutations.append(mutation_name)
                print(
                    f"[MUTATION] {mutation_name} triggered at tick {world_state['tick']}"
                )
                return mutation_name  # One mutation per roll
    return None


def update_vaccine_progress(world_state):
    """
    Vaccine progress advances based on research capacity + GDP + active boosts.
    Drug resistance halves effectiveness unless a counter is developed.
    """
    drug_resistance_active = "drug_resistance" in world_state["active_mutations"]
    counter = world_state["drug_resistance_counter"]
    counter_ready = counter is not None and counter["ticks_remaining"] <= 0

    # Drug resistance penalty -- halved unless counter is ready
    effectiveness = 1.0
    if drug_resistance_active and not counter_ready:
        effectiveness = 0.5

    total_research = 0.0
    for name, country in world_state["countries"].items():
        base = country["research_capacity"] * country["gdp"]

        # Apply active boost multiplier if present
        boost = world_state["research_boosts"].get(name)
        multiplier = boost["multiplier"] if boost else 1.0

        # Research halts if country is heavily infected and unprotected
        if country["infected"] > 0.6 and country["containment_level"] < 0.3:
            multiplier *= 0.5

        total_research += base * multiplier

    vaccine_delta = total_research * 0.0005 * effectiveness
    world_state["global_vaccine_progress"] = min(
        world_state["global_vaccine_progress"] + vaccine_delta, 1.0
    )


def tick_research_boosts(world_state):
    """
    Decrement ticks_remaining on all active research boosts.
    Remove expired boosts.
    """
    expired = []
    for country_name, boost in world_state["research_boosts"].items():
        boost["ticks_remaining"] -= 1
        if boost["ticks_remaining"] <= 0:
            expired.append(country_name)

    for country_name in expired:
        del world_state["research_boosts"][country_name]


def tick_drug_resistance_counter(world_state):
    """
    Decrement drug resistance counter if active.
    """
    counter = world_state["drug_resistance_counter"]
    if counter is None:
        return

    counter["ticks_remaining"] -= 1
    if counter["ticks_remaining"] <= 0:
        # Counter complete -- mark as ready, keep in state so simulation knows
        counter["ticks_remaining"] = 0


def recover_gdp(world_state):
    """
    GDP slowly recovers toward a ceiling based on living population.
    Recovery is slower under active containment.
    """
    for country in world_state["countries"].values():
        # GDP slowly recovers toward a ceiling based on living population
        population_ratio = 1 - (country["dead"] / max(country["population"], 1))
        recovery_rate = 0.001 * population_ratio

        # Recovery is slower under active containment
        if country["containment_level"] > 0.5:
            recovery_rate *= 0.3

        country["gdp"] = min(country["gdp"] + recovery_rate, 1.0)


def apply_spread_tick(world_state):
    """Main tick function. Call this every second from the tick loop.
    Returns mutation name if one occurred, otherwise None."""
    world_state["tick"] += 1

    # get current spread & deaths
    for country_name in world_state["countries"]:
        calculate_spread(country_name, world_state)
        calculate_deaths(country_name, world_state)

    update_vaccine_progress(world_state)
    tick_research_boosts(world_state)
    tick_drug_resistance_counter(world_state)
    recover_gdp(world_state)

    # Mutation check every MUTATION_INTERVAL ticks
    mutation = None
    if world_state["tick"] % MUTATION_INTERVAL == 0:
        mutation = mutation_roll(world_state)

    # Evolution points accumulate for user
    global_infected = sum(
        c["population"] * c["infected"] for c in world_state["countries"].values()
    ) / sum(c["population"] for c in world_state["countries"].values())

    world_state["evolution_points"] += global_infected

    return mutation
