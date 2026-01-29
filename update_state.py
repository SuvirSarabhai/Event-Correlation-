def update_state(state, decision):
    # Update belief
    state["belief"] = decision["belief"]

    # Initialize confidence history safely
    state.setdefault("confidence_history", []).append(decision["confidence"])
