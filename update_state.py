def update_state(state, decision):
    state["belief"] = decision["belief"]
    state["confidence_history"].append(decision["confidence"])
    state["step"] += 1

    if decision["action"] == "COMMIT":
        state["done"] = True

