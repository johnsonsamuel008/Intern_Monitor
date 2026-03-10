import sqlite3
import json
from datetime import datetime, timezone
from client.config import DB_PATH

def connect():
    return sqlite3.connect(str(DB_PATH))

def init_db():
    db = connect()
    c = db.cursor()
    # Adding UNIQUE constraint on (type, payload) to prevent duplicate entries
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            payload TEXT,
            timestamp TEXT NOT NULL, 
            uploaded BOOLEAN DEFAULT 0,
            UNIQUE(type, payload) 
        )
    """)
    db.commit()
    db.close()

def batch_store_logs(log_type, log_list):
    """Efficiently store logs; ignores duplicates based on UNIQUE constraint."""
    db = connect()
    c = db.cursor()
    data_to_insert = []
    for log_data in log_list:
        payload_str = json.dumps(log_data)
        # Use provided timestamp or fallback to current UTC
        timestamp_str = log_data.get('timestamp') or datetime.now(timezone.utc).isoformat()
        data_to_insert.append((log_type, payload_str, timestamp_str))
        
    # 'INSERT OR IGNORE' prevents crashes from duplicate history entries
    c.executemany("INSERT OR IGNORE INTO logs (type, payload, timestamp) VALUES (?, ?, ?)", data_to_insert)
    db.commit()
    db.close()

# Other functions (fetch_pending, mark_uploaded) remain the same.


def fetch_pending(limit=50):
    db = connect()
    c = db.cursor()
    # CRITICAL UPDATE: Select the timestamp column
    c.execute(
        "SELECT id, type, payload, timestamp FROM logs WHERE uploaded = 0 LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    db.close()
    return rows

def mark_uploaded(ids):
    if not ids:
        return
    db = connect()
    c = db.cursor()
    c.executemany(
        # Use standard boolean representation (1 for True, 0 for False)
        "UPDATE logs SET uploaded = 1 WHERE id = ?",
        [(i,) for i in ids]
    )
    db.commit()
    db.close()
