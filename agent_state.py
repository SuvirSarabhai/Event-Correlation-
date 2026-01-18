def init_state():
    return {
        "observations": [],
        "belief": "UNKNOWN",          # UNKNOWN | STABLE | UNSTABLE | CRITICAL
        "confidence_history": [],
        "step": 0,
        "done": False                 # terminal flag
    }
