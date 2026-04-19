import asyncio
from coordinator import run_coordinator
from world_state import world_state
from simulation import apply_spread_tick

COORDINATOR_INTERVAL = 3  # ticks


# async def tick_loop():
#     while world_state["game_status"] is None:
#         # advance simulation
#         apply_spread_tick(world_state)
#
#         # TODO: Broadcast state to frontend
#
#         # run coordinator every N ticks
#         if world_state["tick"] % COORDINATOR_INTERVAL == 0:
#             thought, actions = await run_coordinator(world_state, sio)
#
#             # TODO: add actions
#
#         # check win condition
#         from world_state import check_win_condition
#
#         result = check_win_condition()
#         if result:
#             world_state["game_status"] = result
#             await sio.emit("game_over", {"result": result})


async def main():
    print("Calling Coordinator...")
    thought, actions = await run_coordinator(world_state)
    print(f"\nTHOUGHT:\n{thought}")
    print(f"\nACTIONS:\n{actions}")


if __name__ == "__main__":
    asyncio.run(main())

