import os
import sqlite3
from datetime import datetime, timezone

DATABASE_URL = os.environ.get("DATABASE_URL")


def _conn():
    if DATABASE_URL:
        import psycopg
        return psycopg.connect(DATABASE_URL), "%s"
    return sqlite3.connect(os.environ.get("SQLITE_PATH", "local.db")), "?"


def init():
    conn, _ = _conn()
    with conn:
        if DATABASE_URL:
            conn.execute("CREATE TABLE IF NOT EXISTS rounds (id SERIAL PRIMARY KEY, multiplier DOUBLE PRECISION NOT NULL, added_by TEXT, created_at TEXT NOT NULL)")
        else:
            conn.execute("CREATE TABLE IF NOT EXISTS rounds (id INTEGER PRIMARY KEY AUTOINCREMENT, multiplier REAL NOT NULL, added_by TEXT, created_at TEXT NOT NULL)")
    conn.close()


def add_round(multiplier, added_by):
    conn, p = _conn()
    with conn:
        conn.execute(f"INSERT INTO rounds (multiplier, added_by, created_at) VALUES ({p}, {p}, {p})",
                     (multiplier, added_by, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    conn.close()


def recent(limit=50):
    conn, p = _conn()
    rows = conn.execute(f"SELECT id, multiplier, added_by, created_at FROM rounds ORDER BY id DESC LIMIT {p}", (limit,)).fetchall()
    conn.close()
    return [{"id": r[0], "multiplier": r[1], "added_by": r[2], "created_at": r[3]} for r in rows]


def stats():
    conn, _ = _conn()
    rows = [r[0] for r in conn.execute("SELECT multiplier FROM rounds ORDER BY id").fetchall()]
    conn.close()
    if not rows:
        return {"count": 0}
    streak = 0  # current run of rounds below 2.0x
    for m in reversed(rows):
        if m < 2.0:
            streak += 1
        else:
            break
    return {
        "count": len(rows),
        "average": round(sum(rows) / len(rows), 2),
        "max": max(rows),
        "min": min(rows),
        "pct_below_2x": round(100 * sum(m < 2.0 for m in rows) / len(rows), 1),
        "current_streak_below_2x": streak,
    }
