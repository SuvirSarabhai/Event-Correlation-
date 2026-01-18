import json
from db import get_connection


def save_state(agent_id, state):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO agent_state (agent_id, state)
        VALUES (%s, %s)
        ON CONFLICT (agent_id)
        DO UPDATE SET
            state = EXCLUDED.state,
            updated_at = NOW()
        """,
        (agent_id, json.dumps(state))
    )

    conn.commit()
    cur.close()
    conn.close()


def load_state(agent_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT state FROM agent_state WHERE agent_id = %s",
        (agent_id,)
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return row[0]  # psycopg2 auto-decodes JSONB
    return None
