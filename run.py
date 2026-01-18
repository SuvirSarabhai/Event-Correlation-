from agent_state import init_state
from agent import agent_step
from state_store import load_state, save_state

import pprint

# Unique identity for this agent instance
AGENT_ID = "incident_agent_1"

# 🔹 Load state from Postgres if it exists
state = load_state(AGENT_ID)
if state is None:
    state = init_state()

signals = [
    "fire",
    "fire_growing_rapidly",
    "smoke_heavy",
    "crowd_panicking"
]

for s in signals:
    decision = agent_step(state, s)

    # 🔹 Persist state after every step
    save_state(AGENT_ID, state)

    print("Signal:", s)
    print("Decision:", decision)
    print("State:", state)
    print("-" * 40)

# Final state snapshot
pprint.pprint(state)
