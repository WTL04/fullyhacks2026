from world_state import world_state
from simulation import apply_spread_tick

# Seed one country manually
world_state["countries"]["Brazil"]["infected"] = 0.05

# Run 10 ticks
for i in range(10):
    apply_spread_tick(world_state)
    print(
        f"Tick {i + 1}: Brazil infected={world_state['countries']['Brazil']['infected']:.4f}, dead={world_state['countries']['Brazil']['dead']}"
    )
