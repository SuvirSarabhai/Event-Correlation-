import json
import ollama

# ================================
# SAFE JSON PARSER (ADDED)
# ================================

def safe_json_load(text: str):
    """
    Extracts and parses the first valid JSON object from LLM output.
    Prevents crashes when the model adds extra text.
    """
    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in LLM response:\n{text}")

    return json.loads(text[start:end])


# ================================
# INCIDENT ROUTING (LLM-ONLY)
# ================================

ROUTING_SYSTEM_PROMPT = """
You are an incident correlation engine.

An incident represents an evolving real-world situation,
not a single event type.

IMPORTANT ASSUMPTIONS:
- Early incidents may contain only 1–2 weak signals
- Different event types can belong to the SAME incident
  if they occur in the same area and time window
- Escalation across event types (Fire → Smoke → Crowd → Accident)
  is common and should usually be MERGED

DEFAULT BEHAVIOR:
- If location matches and the incident is recent,
  MERGE unless there is strong evidence it is unrelated
- Create a NEW incident ONLY if the alert clearly represents
  a separate, independent situation

Respond ONLY with valid JSON:
{
  "decision": "MERGE" | "NEW_INCIDENT",
  "incident_id": "string or null",
  "confidence": number between 0 and 1,
  "reasoning": "brief explanation"
}
"""



def route_incident_llm(new_alert, active_incidents):
    prompt = {
        "new_alert": new_alert,
        "active_incidents": active_incidents
    }

    response = ollama.chat(
        model="llama3:latest",
        messages=[
            {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(prompt)}
        ],
        options={"temperature": 0.1}
    )

    return safe_json_load(response["message"]["content"])


# ================================
# INCIDENT REASONING (STATEFUL)
# ================================

REASONING_SYSTEM_PROMPT = """
You are a stateful incident reasoning agent.

Your job is to decide whether the incident has escalated
enough to be COMMITTED.

Belief phases (STRICT):
- STABLE: weak or isolated signals
- UNSTABLE: multiple or escalating signals
- CRITICAL: clear escalation requiring commitment

Rules:
- Belief must escalate gradually
- Use CRITICAL only after multiple severe signals
- COMMIT only when belief is CRITICAL
- Never output UNKNOWN
- Never output MERGE or NEW_INCIDENT
- Never output incident_id

Respond ONLY in valid JSON:
{
  "belief": "STABLE" | "UNSTABLE" | "CRITICAL",
  "confidence": number between 0 and 1,
  "action": "CONTINUE" | "COMMIT",
  "reasoning": "short explanation"
}
"""


def reason_with_llm(state_summary):
    response = ollama.chat(
        model="llama3:latest",
        messages=[
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(state_summary)}
        ],
        options={"temperature": 0.2}
    )

    return safe_json_load(response["message"]["content"])



def reason_with_llm(state_summary):
    response = ollama.chat(
        model="llama3:latest",
        messages=[
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(state_summary)}
        ],
        options={"temperature": 0.2}
    )

    # 🔧 CHANGED LINE (safe parsing)
    return safe_json_load(response["message"]["content"])
