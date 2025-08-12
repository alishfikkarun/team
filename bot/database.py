import sqlite3
import json
from datetime import datetime
import threading
from typing import Optional, Dict, Any

class Database:
    def __init__(self, db_path: str = "gifts.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.init_database()
    
    def get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_path)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection
    
    def init_database(self):
        """Initialize the database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on slug for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gifts_slug ON gifts(slug)
        """)
        
        conn.commit()
    
    def save_gift(self, slug: str, payload_json: str) -> bool:
        """Save a gift to the database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO gifts (slug, payload_json, created_at)
                VALUES (?, ?, ?)
            """, (slug, payload_json, datetime.now()))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Slug already exists
            return False
        except Exception as e:
            print(f"Error saving gift: {e}")
            return False
    
    def get_gift(self, slug: str) -> Optional[Dict[Any, Any]]:
        """Get a gift by slug"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT payload_json, created_at
                FROM gifts
                WHERE slug = ?
            """, (slug,))
            
            row = cursor.fetchone()
            if row:
                payload = json.loads(row['payload_json'])
                return {
                    'payload': payload,
                    'created_at': row['created_at']
                }
            return None
        except Exception as e:
            print(f"Error getting gift: {e}")
            return None
    
    def close(self):
        """Close the database connection"""
        if hasattr(self.local, 'connection'):
            self.local.connection.close()
