import sqlite3
import json
from datetime import datetime, timezone
from dataclasses import asdict
from schema import MemoryEntry

DB_PATH = "/home/stefco/panopticon/panopticon.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            objective TEXT,
            action TEXT,
            vendor_original TEXT,
            cost_original_monthly REAL,
            vendor_recommended TEXT,
            cost_recommended_monthly REAL,
            severity TEXT,
            likelihood TEXT,
            confidence REAL,
            annual_saving REAL,
            outcome TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Memory store initialised.")

def store(entry: MemoryEntry):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO memory (
            agent_id, objective, action,
            vendor_original, cost_original_monthly,
            vendor_recommended, cost_recommended_monthly,
            severity, likelihood, confidence,
            annual_saving, outcome, timestamp
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        entry.agent_id, entry.objective, entry.action,
        entry.vendor_original, entry.cost_original_monthly,
        entry.vendor_recommended, entry.cost_recommended_monthly,
        entry.severity, entry.likelihood, entry.confidence,
        entry.annual_saving, entry.outcome, entry.timestamp
    ))
    conn.commit()
    conn.close()

def recall(action_keyword: str) -> list[dict]:
    """Search memory for past interventions matching a keyword."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT * FROM memory
        WHERE action LIKE ? AND outcome = 'ACCEPTED'
        ORDER BY timestamp DESC
        LIMIT 5
    """, (f"%{action_keyword}%",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def all_entries() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM memory ORDER BY timestamp DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    # Write a test entry
    entry = MemoryEntry(
        agent_id="worker-001",
        objective="launch customer support infrastructure",
        action="purchase email provider",
        vendor_original="Mailchimp Pro",
        cost_original_monthly=199.0,
        vendor_recommended="Brevo",
        cost_recommended_monthly=29.0,
        severity="HIGH",
        likelihood="HIGH",
        confidence=0.92,
        annual_saving=2040.0,
        outcome="ACCEPTED",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    store(entry)
    print("Entry stored.")

    # Recall it
    results = recall("email")
    print(f"Recalled {len(results)} matching entries:")
    for r in results:
        print(f"  → {r['vendor_original']} → {r['vendor_recommended']} | saving ${r['annual_saving']}/yr | confidence {r['confidence']}")
