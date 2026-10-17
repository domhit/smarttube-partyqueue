import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .config import settings

DB = Path('/app/data/partyqueue.db')

@contextmanager
def conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    try:
        yield c
        c.commit()
    finally:
        c.close()

def _has_column(c, table, column):
    return any(row['name'] == column for row in c.execute(f'PRAGMA table_info({table})'))

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
          target_tv TEXT NOT NULL DEFAULT 'default',
          position INTEGER NOT NULL,
          source TEXT DEFAULT 'request',
          status TEXT DEFAULT 'queued',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          started_at TEXT,
          finished_at TEXT
        );
        CREATE TABLE IF NOT EXISTS search_cache (
          query TEXT PRIMARY KEY,
          payload TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT OR IGNORE INTO settings(key,value) VALUES ('queue_locked','false'),('playback_enabled','true');
        """)
        if not _has_column(c, 'queue', 'target_tv'):
            c.execute("ALTER TABLE queue ADD COLUMN target_tv TEXT NOT NULL DEFAULT 'default'")
        c.execute("UPDATE queue SET target_tv=? WHERE target_tv IN ('', 'default')", (settings.default_tv,))
        c.execute('CREATE INDEX IF NOT EXISTS idx_queue_tv_status_position ON queue(target_tv,status,position)')

def setting(key, default=''):
    with conn() as c:
        row = c.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return row['value'] if row else default

def set_setting(key, value):
    with conn() as c:
        c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))
