from observe import observe
from state_summary import summarize_state
from llm_reasoning import reason_with_llm
from update_state import update_state


def agent_step(state, signal):
    # 🚫 Terminal state check
    if state.get("done"):
        state["observations"].append(observe(signal))
        return {
            "message": "Agent already committed (signal logged)",
            "state": state
        }

    # 1️⃣ Observe
    observation = observe(signal)
    state["observations"].append(observation)

    # 2️⃣ Summarize state
    summary = summarize_state(state)

    # 3️⃣ Reason with LLM
    decision = reason_with_llm(summary)

    # 🚧 GATE 1: Minimum evidence gate
    if decision["action"] == "COMMIT" and len(state["observations"]) < 2:
        decision["action"] = "CONTINUE"
        decision["reasoning"] += " | Commit blocked: insufficient observations."

    # 🚧 GATE 2: Belief phase gate (CRITICAL only)
    if decision["action"] == "COMMIT" and decision["belief"] != "CRITICAL":
        decision["action"] = "CONTINUE"
        decision["reasoning"] += " | Commit blocked: belief not CRITICAL."

    # 4️⃣ Update state
    update_state(state, decision)

    return decision
