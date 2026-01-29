import json
from datetime import datetime
import uuid
from db import get_connection


def extract_incident_summary(state, incident_id: str):
    if not state.get("done"):
        raise ValueError("Cannot extract incident summary before commit")

    signals = [obs["signal"] for obs in state.get("observations", [])]

    return {
        "incident_id": incident_id,   # ✅ reuse existing ID
        "final_belief": state.get("belief"),
        "final_confidence": (
            state.get("confidence_history", [])[-1]
            if state.get("confidence_history") else None
        ),
        "signals": signals,
        "num_steps": state.get("step"),
        "committed_at": datetime.utcnow().isoformat(),
    }



def save_incident_summary(summary: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO incident_memory (
            incident_id,
            final_belief,
            final_confidence,
            signals,
            num_steps,
            committed_at,
            summary
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            summary["incident_id"],
            summary["final_belief"],
            summary["final_confidence"],
            json.dumps(summary["signals"]),
            summary["num_steps"],
            summary["committed_at"],
            json.dumps(summary),
        )
    )

    conn.commit()
    cur.close()
    conn.close()


def get_active_incidents():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.incident_id,
            json_agg(
                json_build_object(
                    'event', a.event_type,
                    'severity', a.severity,
                    'confidence', a.confidence,
                    'location', a.area
                )
            ) AS signals
        FROM alerts a
        LEFT JOIN incident_memory im
          ON a.incident_id = im.incident_id
        WHERE a.incident_id IS NOT NULL
          AND im.incident_id IS NULL
          AND a.created_at > NOW() - INTERVAL '2 hours'
        GROUP BY a.incident_id
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "incident_id": row[0],
            "signals": row[1]
        }
        for row in rows
    ]


