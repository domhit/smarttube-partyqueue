import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB = Path('/app/data/partyqueue.db')

@contextmanager
def conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS queue (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          video_id TEXT NOT NULL,
          title TEXT NOT NULL,
          channel TEXT DEFAULT '',
          thumbnail TEXT DEFAULT '',
          duration_seconds INTEGER DEFAULT 0,
          requested_by TEXT DEFAULT 'Gast',
          position INTEGER NOT NULL,
          source TEXT DEFAULT 'request',
          status TEXT DEFAULT 'queued',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          started_at TEXT,
          finished_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_queue_status_position ON queue(status, position);
        CREATE TABLE IF NOT EXISTS search_cache (
          query TEXT PRIMARY KEY,
          payload TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT OR IGNORE INTO settings(key,value) VALUES ('queue_locked','false'),('playback_enabled','true');
        """)

def setting(key, default=''):
    with conn() as c:
        row=c.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return row['value'] if row else default

def set_setting(key,value):
    with conn() as c:
        c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value)))
