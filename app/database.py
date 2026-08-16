import sqlite3
import os
import re
from app.config import DB_PATH
from app.logger import logger

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None

# Custom cursor wrapper to seamlessly translate SQLite queries (?) to Postgres queries (%s)
class DualCursor:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def execute(self, query, params=None):
        if self.is_postgres:
            # Convert SQLite placeholders to Postgres placeholders
            query = query.replace("?", "%s")
            # Convert SQLite AUTOINCREMENT to Postgres SERIAL
            query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
            # Convert TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            # (Postgres handles this fine, but we can be safe)
            
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

class DualConnection:
    def __init__(self, conn, is_postgres):
        self.conn = conn
        self.is_postgres = is_postgres

    def cursor(self):
        cur = self.conn.cursor(cursor_factory=DictCursor) if self.is_postgres else self.conn.cursor()
        return DualCursor(cur, self.is_postgres)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_connection():
    supabase_url = os.environ.get("SUPABASE_URL")
    
    if supabase_url and psycopg2:
        try:
            conn = psycopg2.connect(supabase_url)
            return DualConnection(conn, True)
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}. Falling back to SQLite.")
            
    # Fallback to local SQLite
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return DualConnection(conn, False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create topics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            source TEXT,
            score REAL,
            status TEXT DEFAULT 'DISCOVERED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create research_sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            url TEXT,
            content_summary TEXT,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    ''')
    
    # Create scripts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            raw_script TEXT,
            scenes_json TEXT,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    ''')
    
    # Create videos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            current_stage TEXT,
            status TEXT,
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    ''')
    
    # Create series_state table for multi-part videos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            current_part INTEGER DEFAULT 1,
            total_parts INTEGER DEFAULT 7,
            context_summary TEXT,
            status TEXT DEFAULT 'IN_PROGRESS',
            FOREIGN KEY(topic_id) REFERENCES topics(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

if __name__ == "__main__":
    init_db()
