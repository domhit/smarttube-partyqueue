import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import settings

DB = Path(settings.data_dir) / 'partyqueue.db'

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

def _has_col(c, table, name):
    return any(r['name'] == name for r in c.execute(f'PRAGMA table_info({table})'))

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY AUTOINCREMENT,video_id TEXT NOT NULL,title TEXT NOT NULL,channel TEXT DEFAULT '',thumbnail TEXT DEFAULT '',duration_seconds INTEGER DEFAULT 0,requested_by TEXT DEFAULT 'Gast',target_tv TEXT NOT NULL DEFAULT 'default',position INTEGER NOT NULL,source TEXT DEFAULT 'request',status TEXT DEFAULT 'queued',created_at TEXT DEFAULT CURRENT_TIMESTAMP,started_at TEXT,finished_at TEXT);
        CREATE TABLE IF NOT EXISTS search_cache(query TEXT PRIMARY KEY,payload TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS base_playlist(id INTEGER PRIMARY KEY AUTOINCREMENT,video_id TEXT NOT NULL UNIQUE,title TEXT NOT NULL,channel TEXT DEFAULT '',thumbnail TEXT DEFAULT '',duration_seconds INTEGER DEFAULT 0,enabled INTEGER NOT NULL DEFAULT 1,position INTEGER NOT NULL,added_from TEXT NOT NULL DEFAULT 'manual',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS base_play_history(id INTEGER PRIMARY KEY AUTOINCREMENT,target_tv TEXT NOT NULL,base_item_id INTEGER NOT NULL,played_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS quota_usage(quota_date TEXT PRIMARY KEY,search_api_calls INTEGER NOT NULL DEFAULT 0,search_cache_hits INTEGER NOT NULL DEFAULT 0,search_failures INTEGER NOT NULL DEFAULT 0,quota_exceeded INTEGER NOT NULL DEFAULT 0,playlist_api_calls INTEGER NOT NULL DEFAULT 0,last_search_at TEXT);
        INSERT OR IGNORE INTO settings(key,value) VALUES('queue_locked','false'),('playback_enabled','true'),('base_playlist_enabled','true');
        """)
        if not _has_col(c, 'queue', 'target_tv'):
            c.execute("ALTER TABLE queue ADD COLUMN target_tv TEXT NOT NULL DEFAULT 'default'")
        c.execute("UPDATE queue SET target_tv=? WHERE target_tv IN ('','default')", (settings.default_tv,))
        c.execute('CREATE INDEX IF NOT EXISTS idx_queue_tv_status ON queue(target_tv,status,position)')

def setting(key, default=''):
    with conn() as c:
        row = c.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return row['value'] if row else default

def set_setting(key, value):
    with conn() as c:
        c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, str(value)))
