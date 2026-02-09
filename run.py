from db import get_connection
from state_store import load_state, save_state
from incident_memory import extract_incident_summary, save_incident_summary
from agent import agent_step
from observe import observe
from agent_state import init_state
import uuid


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def fetch_unprocessed_alerts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT alert_id, event_type, severity, confidence, area, incident_id
        FROM alerts
        WHERE processed = false
        ORDER BY created_at ASC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def mark_processed(alert_id, incident_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE alerts
        SET processed = true,
            incident_id = %s
        WHERE alert_id = %s
    """, (incident_id, alert_id))
    conn.commit()
    cur.close()
    conn.close()


def get_latest_active_incident_id(area):
    """
    Reuse most recent incident for the same area.
    THIS is the critical fix.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT incident_id
        FROM alerts
        WHERE area = %s
          AND incident_id IS NOT NULL
          AND processed = true
        ORDER BY created_at DESC
        LIMIT 1
    """, (area,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


# --------------------------------------------------
# Main loop
# --------------------------------------------------

def run():
    alerts = fetch_unprocessed_alerts()
    print(f"\n[START] Alerts to process: {len(alerts)}\n")

    for alert in alerts:
        alert_id, event_type, severity, confidence, area, existing_incident_id = alert

        normalized_alert = {
            "event": event_type,
            "severity": severity,
            "confidence": confidence,
            "location": area
        }

        # --------------------------------------------------
        # INCIDENT RESOLUTION (AREA-BASED, NOT LLM)
        # --------------------------------------------------
        incident_id = existing_incident_id

        if not incident_id:
            incident_id = get_latest_active_incident_id(area)

        if incident_id:
            state = load_state(incident_id) or init_state()
        else:
            incident_id = str(uuid.uuid4())
            state = init_state()

        # --------------------------------------------------
        # Observe + accumulate
        # --------------------------------------------------
        signal = observe(normalized_alert)
        state.setdefault("observations", []).append(signal)

        # --------------------------------------------------
        # Agent reasoning
        # --------------------------------------------------
        decision = agent_step(state, signal)

        # --------------------------------------------------
        # CLEAN OUTPUT (READABLE)
        # --------------------------------------------------
        print("-" * 60)
        print(f"INCIDENT ID : {incident_id}")
        print(f"OBS COUNT   : {len(state['observations'])}")
        print(
            f"SIGNAL      : {event_type} | {severity} | "
            f"conf={confidence} | {area}"
        )
        print(f"BELIEF      : {decision.get('belief')}")
        print(f"CONFIDENCE  : {decision.get('confidence')}")
        print(f"ACTION      : {decision.get('action')}")
        print(f"REASONING   : {decision.get('reasoning')}")

        # --------------------------------------------------
        # FIX: Set state["done"] when action is COMMIT
        # --------------------------------------------------
        if decision.get('action') == 'COMMIT':
            state["done"] = True

        # --------------------------------------------------
        # Commit once
        # --------------------------------------------------
        if state.get("done") and not state.get("_committed"):
            summary = extract_incident_summary(state, incident_id)
            save_incident_summary(summary)
            state["_committed"] = True
            print(f"\n[COMMIT] ✅ Incident saved to incident_memory: {incident_id}")

        # --------------------------------------------------
        # Persist
        # --------------------------------------------------
        save_state(incident_id, state)
        mark_processed(alert_id, incident_id)

    print("\n[END] Run complete\n")


if __name__ == "__main__":
    run()