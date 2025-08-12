# bot/db.py
import sqlite3
import json
import datetime
from typing import Optional

DB_PATH = "data/gifts.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        payload_json TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_gift(slug: str, payload: dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO gifts (slug, payload_json, created_at) VALUES (?, ?, ?)",
        (slug, json.dumps(payload, ensure_ascii=False), datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def get_gift(slug: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT payload_json FROM gifts WHERE slug = ?", (slug,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row[0])
