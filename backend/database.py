"""
Database layer using SQLite.

Why SQLite for v1: zero setup (no separate server to run), the file
lives right next to your code, and it handles way more load than
you'll need for your first 10-50 customers. Swap to Postgres later
by changing the connection string if you ever outgrow it.

We use raw sqlite3 (no ORM) on purpose: with only 2 tables, an ORM
adds a layer of abstraction you'd have to learn for no real benefit.
You'll see exactly what SQL is running, which matters when you're
learning the wiring.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "reviews.db"


def init_db():
    """Create tables if they don't exist yet. Safe to call every startup."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # One row per business you onboard.
    # slug = the unguessable token used in the dashboard link, e.g. /dashboard/biz_a8f3k2
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            google_place_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # One row per review we've pulled + the AI-drafted response for it.
    # google_review_id lets us avoid inserting duplicates every time we re-fetch.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            google_review_id TEXT NOT NULL,
            author_name TEXT,
            rating INTEGER,
            review_text TEXT,
            review_time TEXT,
            drafted_response TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses (id),
            UNIQUE(business_id, google_review_id)
        )
    """)

    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """
    Context manager so every route gets a connection and it always
    closes, even if an error happens mid-request. Usage:

        with get_db() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["name"]
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
