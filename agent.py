from state_summary import summarize_state
from llm_reasoning import reason_with_llm
from update_state import update_state

VALID_BELIEFS = {"STABLE", "UNSTABLE", "CRITICAL"}
BELIEF_RANK = {"STABLE": 0, "UNSTABLE": 1, "CRITICAL": 2}


def agent_step(state, signal):
    # 🚫 Terminal state
    if state.get("done"):
        return {"message": "Agent already committed", "state": state}

    # 🔍 SAFE DEBUG (state exists here)
    print("OBS COUNT:", len(state.get("observations", [])))

    # 1️⃣ Step counter
    state["step"] = state.get("step", 0) + 1

    # 2️⃣ Summarize + LLM
    summary = summarize_state(state)
    decision = reason_with_llm(summary)

    # 3️⃣ HARDEN decision
    decision.setdefault("belief", "STABLE")
    decision.setdefault("confidence", 0.5)
    decision.setdefault("reasoning", "No reasoning provided")

    # ❌ Remove routing junk
    decision.pop("decision", None)
    decision.pop("incident_id", None)

    # 🔒 SANITIZE PREVIOUS BELIEF
    prev_belief = state.get("belief", "STABLE")
    if prev_belief not in VALID_BELIEFS:
        prev_belief = "STABLE"
        state["belief"] = "STABLE"

    # 🔒 SANITIZE LLM BELIEF
    llm_belief = decision.get("belief")
    if llm_belief not in VALID_BELIEFS:
        llm_belief = prev_belief
        decision["reasoning"] += " | Invalid belief ignored."

    # 🔒 Monotonic escalation
    if BELIEF_RANK[llm_belief] < BELIEF_RANK[prev_belief]:
        decision["belief"] = prev_belief
        decision["reasoning"] += " | Belief downgrade prevented."
    else:
        decision["belief"] = llm_belief

    # 4️⃣ Update state
    update_state(state, decision)

    # 5️⃣ DETERMINISTIC COMMIT RULE (THIS WILL FIRE)
    observations = state.get("observations", [])
    latest = observations[-1]["signal"]

    should_commit = (
        len(observations) >= 2 and
        latest["severity"] == "Severe" and
        decision["confidence"] >= 0.8 and
        decision["belief"] in {"UNSTABLE", "CRITICAL"}
    )

    if should_commit:
        state["done"] = True
        decision["action"] = "COMMIT"
        decision["reasoning"] += " | Commit triggered by escalation rule."
    else:
        decision["action"] = "CONTINUE"

    print("FINAL decision:", decision)
    return decision
