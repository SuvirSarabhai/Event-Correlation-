def summarize_state(state):
    """
    Create a compact, decision-focused summary of the agent's state
    to be passed to the LLM for reasoning.
    """

    # Take only the most recent observations (short-term memory)
    recent_observations = state["observations"][-3:]

    # Extract just the signal values
    recent_signals = [obs["signal"] for obs in recent_observations]

    # Capture confidence trend (how belief is evolving)
    confidence_trend = state["confidence_history"][-3:]

    return {
        "current_belief": state["belief"],
        "recent_signals": recent_signals,
        "confidence_trend": confidence_trend,
        "step": state["step"]
    }
