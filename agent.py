from state_summary import summarize_state
from llm_reasoning import reason_with_llm
from update_state import update_state

VALID_BELIEFS = {"STABLE", "UNSTABLE", "CRITICAL"}
BELIEF_RANK = {
    "STABLE": 0,
    "UNSTABLE": 1,
    "CRITICAL": 2
}


def agent_step(state, signal):
    """
    Pure reasoning engine.
    - NO database writes
    - NO persistence flags
    - Only returns decision
    """

    obs_count = len(state.get("observations", []))
    print(f"[AGENT] Observations so far: {obs_count}")

    # Step counter
    state["step"] = state.get("step", 0) + 1

    # Summarize for LLM
    summary = summarize_state(state)
    decision = reason_with_llm(summary)

    # Harden output
    decision.setdefault("belief", state.get("belief", "STABLE"))
    decision.setdefault("confidence", 0.5)
    decision.setdefault("reasoning", "No reasoning provided")

    # Strip routing junk
    decision.pop("decision", None)
    decision.pop("incident_id", None)

    # Sanitize beliefs
    prev_belief = state.get("belief", "STABLE")
    if prev_belief not in VALID_BELIEFS:
        prev_belief = "STABLE"
        state["belief"] = "STABLE"

    llm_belief = decision.get("belief")
    if llm_belief not in VALID_BELIEFS:
        llm_belief = prev_belief
        decision["reasoning"] += " | Invalid belief ignored."

    if BELIEF_RANK[llm_belief] < BELIEF_RANK[prev_belief]:
        decision["belief"] = prev_belief
        decision["reasoning"] += " | Belief downgrade prevented."
    else:
        decision["belief"] = llm_belief

    # Update state
    update_state(state, decision)

    # Deterministic commit rule
    observations = state.get("observations", [])
    severe_seen = any(o["signal"]["severity"] == "Severe" for o in observations)

    should_commit = (
        len(observations) >= 2
        and severe_seen
        and decision["confidence"] >= 0.8
        and decision["belief"] in {"UNSTABLE", "CRITICAL"}
    )

    if should_commit:
        decision["action"] = "COMMIT"
        decision["reasoning"] += " | Commit triggered by escalation rule."
        print("[AGENT] COMMIT triggered")
    else:
        decision["action"] = "CONTINUE"

    print(
        f"[AGENT] belief={decision['belief']} "
        f"conf={decision['confidence']} "
        f"action={decision['action']}"
    )

    return decision