CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    metric TEXT,
    value REAL,
    severity TEXT,
    explanation TEXT,
    suggested_fix TEXT
);
