def summarize_state(state):
    """
    Create a compact, evidence-focused summary of the agent's state
    to be passed to the LLM for reasoning.
    """

    MAX_OBS = 3  # short-term memory window

    # Take the most recent observations (evidence, not conclusions)
    recent_observations = state.get("observations", [])[-MAX_OBS:]

    # Confidence trend (belief evolution)
    confidence_history = state.get("confidence_history", [])[-MAX_OBS:]

    return {
        # Evidence timeline (what happened)
        "observations": recent_observations,

        # Current stance of the agent
        "belief": state.get("belief"),

        # How confidence is trending
        "confidence_history": confidence_history,

        # Step count (helps LLM reason about progression)
        "step": state.get("step", 0)
    }
