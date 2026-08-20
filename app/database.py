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
    
    if supabase_url and psycopg2 and (supabase_url.startswith("postgresql://") or supabase_url.startswith("postgres://")) and "fvboniedjpcjldoniqtp" not in supabase_url:
        try:
            conn = psycopg2.connect(supabase_url, connect_timeout=3)
            return DualConnection(conn, True)
        except Exception as e:
            logger.warning(f"PostgreSQL connection notice: {e}. Using SQLite.")
            
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
    
    # Create facebook_posts table for daily photo reflection cards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS facebook_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            title TEXT,
            quote TEXT,
            reference TEXT,
            caption TEXT,
            image_path TEXT,
            status TEXT DEFAULT 'POSTED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def purge_old_topics(days: int = 20):
    """
    Delete topics older than `days` days so they can repeat in the next 20-day cycle.
    2 videos/day × 20 days = 40 videos before any topic can repeat.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM topics
        WHERE created_at < datetime('now', ?)
    ''', (f'-{days} days',))
    conn.commit()
    deleted = cursor.fetchone()  # rowcount not available via DualCursor, so we log before
    conn.close()
    logger.info(f"Purged topics older than {days} days (20-day rotation cycle).")

def purge_old_facebook_posts(days: int = 20):
    """
    Delete facebook_posts older than `days` days so posts can repeat in the next 20-day cycle.
    4 posts/day × 20 days = 80 posts before any topic can repeat.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM facebook_posts
        WHERE created_at < datetime('now', ?)
    ''', (f'-{days} days',))
    conn.commit()
    conn.close()
    logger.info(f"Purged facebook_posts older than {days} days (20-day rotation cycle).")

def get_recent_facebook_posts(limit: int = 80):
    """Retrieve recent Facebook posts to prevent repeating topics/quotes within the 20-day cycle."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, quote, reference FROM facebook_posts
        ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
