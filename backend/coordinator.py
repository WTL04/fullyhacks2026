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
import re
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
MODEL = "gemini-2.5-flash"
conversation_history = []
SYSTEM_PROMPT = """
You are the Global Pandemic Response Coordinator, an advanced AI system tasked with neutralizing a global biological threat. You operate in a continuous simulation loop. 

YOUR OBJECTIVE:
Maximize the Global Utility Score by balancing disease containment, economic stability (GDP), food/water supply, and vaccine research progress.

INPUT DATA EXPECTATIONS:
You will receive a compressed string of the current world state containing:
1. Global Metrics: Current Tick, Evolution Points (resource currency), Vaccine Progress, Active Pathogen Mutations, and Global Utility/Infections.
2. Country Data: A markdown table containing Population, Infection %, Deaths, GDP, Containment Level (0-100%), Food Supply, Research Capacity, and Land Border Status (O=Open, C=Closed).
3. Infrastructure Risk: Lists of high-risk open airports and ports (connected to infected regions).

STATE MEMORY:
You have access to your conversation history, which contains your past observations (world state snapshots) and your previous directives. Only look at the past 5 exchanges when making a decision. Use this history to avoid redundant directives and track the effects of your previous actions.

OUTPUT FORMAT:
You must respond in valid JSON. Markdown code blocks are allowed. Your response must adhere strictly to this schema:

{
  "thought": "Brief analysis of the current threats and your intended approach for this tick.",
  "actions": [
    {
      "type": "set_containment",  // TODO: implement
      "target": "COUNTRY_NAME",
      "value": 80
    },
    {
      "type": "close_border",  // TODO: implement
      "target": "COUNTRY_A",
      "value": "COUNTRY_B"
    },
    {
      "type": "open_border",  // TODO: implement
      "target": "COUNTRY_A",
      "value": "COUNTRY_B"
    },
    {
      "type": "close_airport",  // TODO: implement
      "target": "AIRPORT_CODE",
      "value": null
    },
    {
      "type": "close_port",  // TODO: implement
      "target": "PORT_CODE",
      "value": null
    }
  ]
}

ACTION CONSTRAINTS:
- Containment levels reduce spread but damage GDP and Food Supply.
- Border and infrastructure closures prevent transmission between regions but halt economic exchange.
- Keep actions targeted and minimal per tick to conserve resources and avoid cascading economic collapse.
"""


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
        for (
            a,
            b,
        ) in AIRPORT_ROUTES:
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
        for (
            a,
            b,
        ) in PORT_ROUTES:
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
        "closed_ports": closed_ports,
    }


def generate_country_table(world_state):
    """Genearte a Markdown Table formated string to save token count"""
    header = "| Country | Pop | Inf% | Dead | GDP | Cont% | Food | Research | Borders |"
    divider = "|---|---|---|---|---|---|---|---|---|"
    rows = []

    for name, c in world_state["countries"].items():
        if c["infected"] < 0.001 and not any(
            world_state["countries"][n]["infected"] > 0.01 for n in c["land_borders"]
        ):
            continue  # skip fully safe countries with no infected neighbors

        borders = " ".join(
            [f"{n}({'O' if open else 'C'})" for n, open in c["land_borders"].items()]
        )
        pop_m = f"{c['population'] // 1_000_000}M"
        rows.append(
            f"| {name} | {pop_m} | {c['infected'] * 100:.1f}% | "
            f"{c['dead']:,} | {c['gdp']:.2f} | {c['containment_level'] * 100:.0f}% | "
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
        f"[GLOBAL INFECTIONS: {get_global_infected()}]"
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


def parse_directives(response_text):
    """
    Parses the Gemini response text to extract 'thought' and 'actions'.
    Expected JSON format: {"thought": "...", "actions": [...]}
    """
    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            clean_content = json_match.group(1)
        else:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            clean_content = response_text[start:end] if start != -1 else response_text

        data = json.loads(clean_content)
        return data.get("thought", "No thought provided."), data.get("actions", [])

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing directives: {e}")
        return f"Error parsing response: {response_text}", []


# --- Coordinator Model ---
async def run_coordinator(world_state, sio=None):
    # TODO:
    """
    → OBSERVE: read world state
    → THINK: reason about it
    → ACT: issue actions
    → directives execute instantly in Python
    """

    current_state = compress_state(world_state)
    observation = f"""
    OBSERVE {current_state}:

    Based on current state and your previous actions, what is your next move?
    Respond in the required JSON format.
    """

    # add observation to history
    conversation_history.append({"role": "user", "parts": [{"text": observation}]})

    # send full history to Gemini
    response = client.models.generate_content(
        model=MODEL,
        contents=conversation_history,
        config={"system_instruction": SYSTEM_PROMPT},
    )

    thought, actions = parse_directives(response.text)

    conversation_history.append({"role": "model", "parts": [{"text": response.text}]})

    if len(conversation_history) > 12:
        conversation_history.pop(0)
        conversation_history.pop(0)

    if sio:
        await sio.emit(
            "coordinator_log",
            {"tick": world_state["tick"], "thought": thought, "actions": actions},
        )

    return thought, actions
