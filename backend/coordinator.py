"""
TODO:

coordinator.py
│
├── CONSTANTS & CLIENT SETUP
│   ├── genai client initialization
│   └── SYSTEM_PROMPT
│
├── STATE COMPRESSION HELPERS
│   ├── generate_country_table(world_state)
│   ├── get_infrastructure_risks(world_state)
│   └── compress_state(world_state)          ← calls the two above
│
├── RESPONSE PARSING
│   └── parse_directives(response_text)
│
├── CONVERSATION HISTORY
│   └── conversation_history = []            ← module-level list
│
└── MAIN ENTRY POINT
    └── run_coordinator(world_state, sio)    ← called by tick loop in main.py
                ├── calls compress_state()
                ├── calls Gemini API
                ├── calls parse_directives()
                ├── emits to sio
                └── returns thought, actions

"""

import os
import json
from dotenv import load_dotenv
from google import genai
from world_state import (
    get_utility_score,
    get_global_infected,
    world_state,
    AIRPORTS,
    AIRPORT_ROUTES,
    PORTS,
    PORT_ROUTES,
)

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = "gemini-2.5-flash"
conversation_history = []


# --- World Information ---
def get_infrastructure_risks(world_state):
    high_risk_airports = []
    high_risk_ports = []
    closed_airports = []
    closed_ports = []

    for code, airport in AIRPORTS.items():
        # track current closed airports
        if not world_state["airport_status"].get(code, True):
            closed_airports.append(code)
            continue

        # check if any route connects to an infected country
        for a, b, in AIRPORT_ROUTES:
            other = b if a == code else (a if b == code else None)
            if other:
                other_country = AIRPORTS[other]["country"]
                if world_state["countries"][other_country]["infected"] > 0.01:
                    high_risk_airports.append(f"{code} ({airport['country']})")
                    break

    for code, port in PORTS.items():
        # track current closed ports
        if not world_state["port_status"].get(code, True):
            closed_ports.append(code)
            continue 

        # check if any routes connect to an infected country
        for a, b, in PORT_ROUTES:
            other = b if a == code else (a if b == code else None)
            if other:
                other_country = PORTS[other]["country"]
                if world_state["countries"][other_country]["infected"] > 0.01:
                    high_risk_ports.append(f"{code} ({port['country']})")
                    break

    return {
        "high_risk_airports_open": high_risk_airports,
        "high_risk_ports_open": high_risk_ports,
        "closed_airports": closed_airports,
        "closed_ports": closed_ports
    }

def generate_country_table(world_state):
    """ Genearte a Markdown Table formated string to save token count """
    header = "| Country | Pop | Inf% | Dead | GDP | Cont% | Food | Research | Borders |"
    divider = "|---|---|---|---|---|---|---|---|---|"
    rows = []

    for name, c in world_state["countries"].items():
        if c["infected"] < 0.001 and not any(
            world_state["countries"][n]["infected"] > 0.01
            for n in c["land_borders"]
        ):
            continue  # skip fully safe countries with no infected neighbors

        borders = " ".join([
            f"{n}({'O' if open else 'C'})"
            for n, open in c["land_borders"].items()
        ])
        pop_m = f"{c['population']//1_000_000}M"
        rows.append(
            f"| {name} | {pop_m} | {c['infected']*100:.1f}% | "
            f"{c['dead']:,} | {c['gdp']:.2f} | {c['containment_level']*100:.0f}% | "
            f"{c['food_water_supply']:.2f} | {c['research_capacity']} | {borders} |"
        )

    return "\n".join([header, divider] + rows)


def compress_state(world_state):
    """Compresses world state to a string with all relavant world information"""
    header = (
        f"[TICK: {world_state['tick']}] "
        f"[EVO_PTS: {world_state['evolution_points']:.1f}] "
        f"[VAC_PROG: {world_state['global_vaccine_progress'] * 100:.0f}%] "
        f"[MUTATIONS: {', '.join(world_state['active_mutations']) or 'none'}] "
        f"[UTILITY: {get_utility_score():.3f}]"
    )

    country_table = generate_country_table(world_state)
    infrastructure_risk = get_infrastructure_risks(world_state)

    risk_summary = (
        f"High Risk Open - Airports: {', '.join(infrastructure_risk['high_risk_airports_open']) or 'none'}\n"
        f"High Risk Open - Ports: {', '.join(infrastructure_risk['high_risk_ports_open']) or 'none'}\n"
        f"Closed - Airports: {', '.join(infrastructure_risk['closed_airports']) or 'none'}\n"
        f"Closed - Ports: {', '.join(infrastructure_risk['closed_ports']) or 'none'}"
    )

    return f"{header}\n\n{country_table}\n\nINFRASTRUCTURE RISK:\n{risk_summary}"


# --- Coordinator Model --- 
async def run_coordinator(world_state, sio=None):
    # TODO:
    """
    → OBSERVE: read world state
    → THINK: reason about it
    → ACT: issue directives
    → directives execute instantly in Python
    """

    current_state = compress_state(world_state)
    return current_state

if __name__ == "__main__":
    print(compress_state(world_state))
