import json
import aiosqlite
from typing import Optional
from .config import cfg


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS gifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(CREATE_TABLE_SQL)
            await db.commit()

    async def save_gift(self, slug: str, payload: dict) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "INSERT INTO gifts (slug, payload_json) VALUES (?, ?)",
                (slug, json.dumps(payload, ensure_ascii=False)),
            )
            await db.commit()
            return cur.lastrowid

    async def get_gift_by_slug(self, slug: str) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT payload_json FROM gifts WHERE slug = ?", (slug,))
            row = await cur.fetchone()
            if not row:
                return None
            try:
                return json.loads(row[0])
            except Exception:
                return None


db = Database(cfg.DB_PATH)
