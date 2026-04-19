# backend/coordinator.py
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
│   └── chat_session                              ← managed by SDK
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
from backend.world_state import (
    get_utility_score,
    get_global_infected,
    world_state,
)

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = ["gemini-2.5-flash", "gemma-4-31b-it"]
MODEL = models[1]
SYSTEM_PROMPT = """
You are the Global Pandemic Response Coordinator, an advanced AI system tasked with neutralizing a global biological threat. You operate in a continuous simulation loop.

YOUR OBJECTIVE:
Maximize the Global Utility Score by balancing disease containment, economic stability (GDP), food/water supply, and vaccine research progress.

INPUT DATA EXPECTATIONS:
You will receive a compressed string of the current world state containing:
1. Global Metrics: Current Tick, Evolution Points (resource currency), Vaccine Progress, Active Pathogen Mutations, and Global Utility/Infections.
2. Country Data: A markdown table containing Population, Infection %, Deaths, GDP, Containment Level (0-100%), Food Supply, Research Capacity, and Land Border Status (O=Open, C=Closed).
3. Infrastructure Risk: Lists of high-risk open airports and ports (connected to infected regions).
4. Research Status: Active research boosts per country, shared data pairs already used, and drug resistance counter progress if active.

STATE MEMORY:
You have access to your conversation history, which contains your past observations (world state snapshots) and your previous directives. Only look at the past 5 exchanges when making a decision. Use this history to avoid redundant directives and track the effects of your previous actions.

OUTPUT FORMAT:
You must respond in valid JSON. Markdown code blocks are allowed. Your response must adhere strictly to this schema:
{
  "thought": "Brief analysis of the current threats and your intended approach for this tick.",
  "actions": [
    {
      "type": "set_containment",
      "target": "COUNTRY_NAME",
      "value": 80
    },
    {
      "type": "close_border",
      "target": "COUNTRY_A",
      "value": "COUNTRY_B"
    },
    {
      "type": "open_border",
      "target": "COUNTRY_A",
      "value": "COUNTRY_B"
    },
    {
      "type": "close_airport",
      "target": "COUNTRY_NAME",
      "value": null
    },
    {
      "type": "close_port",
      "target": "COUNTRY_NAME",
      "value": null
    },
    {
      "type": "fund_research",
      "target": "COUNTRY_NAME",
      "value": 2
    },
    {
      "type": "share_data",
      "target": "COUNTRY_A",
      "value": "COUNTRY_B"
    },
    {
      "type": "develop_counter",
      "target": "COUNTRY_NAME",
      "value": null
    },
    {
      "type": "foreign_aid",
      "target": "DONOR_COUNTRY",
      "value": "RECIPIENT_COUNTRY"
    },
    {
      "type": "reduce_containment",
      "target": "COUNTRY_NAME",
      "value": 20
    }
  ]
}
 
ACTION CONSTRAINTS:
 
Containment:
- set_containment value is 0-100 (integer). Higher values reduce spread but cost GDP and food supply.
- close_border / open_border block or restore land transmission between neighbors.
- close_airport / close_port block long-range air or sea transmission. Use COUNTRY_NAME.
- reduce_containment lowers containment on a country to recover GDP. 
  Use when GDP falls below 0.20 and spread is stable. 
  Accepts higher transmission risk in exchange for economic recovery.

Research:
- fund_research boosts a country's vaccine research output by value multiplier (1.1-3.0) for 10 ticks. Costs 10% GDP. Country must have research_capacity > 0. If a boost is already active, it extends duration instead of overwriting.
- share_data triggers a one-time +2% global vaccine progress between two countries. Costs 5% GDP from the initiating country. Both countries must have research_capacity > 0. Each country pair can only share data ONCE per game -- check Research Status before issuing this action.
- develop_counter is only valid when drug_resistance mutation is active. Costs 20% GDP. Takes 14 ticks to restore full vaccine effectiveness. Only one counter can be in development at a time.

Foreign Aid:
- foreign_aid transfers GDP from a wealthy donor to a struggling recipient.
  target = donor, value = recipient.
- Donor must have GDP > 0.40. Transfer costs 15% of donor GDP.
  Recipient gains approximately 10% GDP (logistics overhead applies).
- Use when a low-GDP country has active infection but cannot fund 
  its own containment or research.
- Prefer foreign_aid over triage. Abandoning a country accelerates 
  global spread through open borders. Keeping all countries economically 
  viable is the optimal long-term strategy.
- Do not send aid to a country with GDP already above 0.50.

TRIAGE PROTOCOL:
- If a country's GDP falls below 0.10 and infection exceeds 20%, 
  classify it as a SACRIFICE ZONE.
- In a SACRIFICE ZONE: open borders to reduce GDP drain, 
  remove containment, and redirect any remaining resources 
  to high-GDP high-research countries.
- Explicitly state in your thought when you are implementing triage.

General:
- Keep actions targeted and minimal per tick to conserve resources and avoid cascading economic collapse.
- Do not close borders or airports to countries with less than 1% infection.
- Do not fund research in countries with GDP below 0.15.
- Do not issue develop_counter if drug_resistance is not in active mutations.
- Do not share_data between a pair already listed in shared_data_pairs.
- Prioritize containment early game, shift toward research once global infection exceeds 20%.
"""

# Initialize chat session to handle history automatically
chat_session = client.chats.create(
    model=MODEL, config={"system_instruction": SYSTEM_PROMPT}
)


# --- World Information ---
def get_infrastructure_risks(world_state):
    high_risk_airports = []
    high_risk_ports = []
    closed_airports = []
    closed_ports = []

    countries = world_state["countries"]

    for name, c in countries.items():
        # Airports
        if not c.get("airports_open", True):
            closed_airports.append(name)
        elif any(other["infected"] > 0.01 for other_name, other in countries.items() if other_name != name):
            high_risk_airports.append(name)

        # Ports
        if not c.get("ports_open", True):
            closed_ports.append(name)
        elif any(other["infected"] > 0.01 for other_name, other in countries.items() if other_name != name):
            high_risk_ports.append(name)

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
    """Compresses world state to a string with all relevant world information"""
    header = (
        f"[TICK: {world_state['tick']}] "
        f"[EVO_PTS: {world_state['evolution_points']:.1f}] "
        f"[VAC_PROG: {world_state['global_vaccine_progress'] * 100:.0f}%] "
        f"[MUTATIONS: {', '.join(world_state['active_mutations']) or 'none'}] "
        f"[UTILITY: {get_utility_score():.3f}] "
        f"[GLOBAL INFECTIONS: {get_global_infected():.3f}]"
    )

    # Aid opportunities
    aid_needed = [
        name
        for name, c in world_state["countries"].items()
        if c["gdp"] < 0.20 and c["infected"] > 0.01
    ]
    aid_capable = [
        name for name, c in world_state["countries"].items() if c["gdp"] > 0.40
    ]
    if aid_needed:
        header += (
            f"\n[AID NEEDED: {', '.join(aid_needed)}] "
            f"[AID CAPABLE: {', '.join(aid_capable) or 'none'}]"
        )

    # Include last cycle failures for coordinator feedback
    last_results = world_state.get("last_action_results", [])
    failed = [r for r in last_results if r.get("status") == "failed"]
    if failed:
        failures_str = ", ".join(
            f"{r['target']} ({r.get('message', 'unknown')})" for r in failed
        )
        header += f"\n[LAST CYCLE FAILURES: {failures_str}]"

    country_table = generate_country_table(world_state)

    infrastructure_risk = get_infrastructure_risks(world_state)
    risk_summary = (
        f"High Risk Open - Airports: {', '.join(infrastructure_risk['high_risk_airports_open']) or 'none'}\n"
        f"High Risk Open - Ports: {', '.join(infrastructure_risk['high_risk_ports_open']) or 'none'}\n"
        f"Closed - Airports: {', '.join(infrastructure_risk['closed_airports']) or 'none'}\n"
        f"Closed - Ports: {', '.join(infrastructure_risk['closed_ports']) or 'none'}"
    )

    # Research status section
    active_boosts = world_state.get("research_boosts", {})
    boost_summary = (
        ", ".join(
            f"{country}: {boost['multiplier']}x ({boost['ticks_remaining']} ticks left)"
            for country, boost in active_boosts.items()
        )
        or "none"
    )

    shared_pairs = world_state.get("shared_data_pairs", [])
    shared_summary = ", ".join(shared_pairs) or "none"

    counter = world_state.get("drug_resistance_counter")
    if counter is None:
        counter_summary = "not started"
    elif counter["ticks_remaining"] <= 0:
        counter_summary = "complete -- vaccine effectiveness restored"
    else:
        counter_summary = f"{counter['ticks_remaining']} ticks remaining"

    research_summary = (
        f"Active Boosts: {boost_summary}\n"
        f"Shared Data Pairs Used: {shared_summary}\n"
        f"Drug Resistance Counter: {counter_summary}"
    )

    return (
        f"{header}\n\n"
        f"{country_table}\n\n"
        f"INFRASTRUCTURE RISK:\n{risk_summary}\n\n"
        f"RESEARCH STATUS:\n{research_summary}"
    )


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
    → ACT: issue directives
    → directives execute instantly in Python
    """

    current_state = compress_state(world_state)
    observation = f"""
    OBSERVE {current_state}:

    Based on current state and your previous actions, what is your next move?
    Respond in the required JSON format.
    """

    # Use the chat session to send the observation
    # chat_session.send_message handles history automatically
    response = chat_session.send_message(observation)

    thought, actions = parse_directives(response.text)

    if sio:
        await sio.emit(
            "coordinator_log",
            {"tick": world_state["tick"], "thought": thought, "actions": actions},
        )

    return thought, actions
