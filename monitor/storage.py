"""
This is where I keep everything on one local file using SQLite.
There is nothing extra to install and nothing to set up, and it
works the same way on every computer.
"""

import sqlite3
import time
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "monitor.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            temperature_c REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            metric TEXT,
            value REAL,
            severity TEXT,
            explanation TEXT,
            suggested_fix TEXT,
            sent_to_cloud INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_reading(reading):
    conn = get_connection()
    conn.execute(
        "INSERT INTO readings (timestamp, cpu_percent, memory_percent, disk_percent, temperature_c) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            reading["timestamp"],
            reading["cpu_percent"],
            reading["memory_percent"],
            reading["disk_percent"],
            reading["temperature_c"],
        ),
    )
    # I only keep the most recent 24 hours of readings so the file does not grow forever
    cutoff = time.time() - (24 * 60 * 60)
    conn.execute("DELETE FROM readings WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()


def get_latest_reading():
    conn = get_connection()
    row = conn.execute("SELECT * FROM readings ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None


def save_anomaly(metric, value, severity, explanation="", suggested_fix=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO anomalies (timestamp, metric, value, severity, explanation, suggested_fix) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (time.time(), metric, value, severity, explanation, suggested_fix),
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return row_id


def get_recent_anomalies(limit=25):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM anomalies ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_unsent_anomalies():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM anomalies WHERE sent_to_cloud = 0").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_anomaly_sent(anomaly_id):
    conn = get_connection()
    conn.execute("UPDATE anomalies SET sent_to_cloud = 1 WHERE id = ?", (anomaly_id,))
    conn.commit()
    conn.close()


def set_state(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO state (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, json.dumps(value)),
    )
    conn.commit()
    conn.close()


def get_state(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
    conn.close()
    return json.loads(row["value"]) if row else default


if __name__ == "__main__":
    init_db()
    print("database ready at", DB_PATH)
