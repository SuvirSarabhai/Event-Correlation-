import json
from db import get_connection


def save_state(incident_id, state):
    if incident_id is None:
        raise ValueError("incident_id cannot be None when saving state")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO agent_state (agent_id, state, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (agent_id)
        DO UPDATE SET
            state = EXCLUDED.state,
            updated_at = NOW()
    """, (incident_id, json.dumps(state)))

    conn.commit()
    cur.close()
    conn.close()


def load_state(incident_id):
    if incident_id is None:
        return None

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT state
        FROM agent_state
        WHERE agent_id = %s
    """, (incident_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    return row[0] if row else None
