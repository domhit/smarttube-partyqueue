import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import settings
DB=Path(settings.data_dir)/'partyqueue.db'
@contextmanager
def conn():
 DB.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA foreign_keys=ON')
 try: yield c; c.commit()
 finally: c.close()
def col(c,t,n): return any(r['name']==n for r in c.execute(f'PRAGMA table_info({t})'))
def init_db():
 with conn() as c:
  c.executescript("""
  CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY AUTOINCREMENT,video_id TEXT NOT NULL,title TEXT NOT NULL,channel TEXT DEFAULT '',thumbnail TEXT DEFAULT '',duration_seconds INTEGER DEFAULT 0,requested_by TEXT DEFAULT 'Gast',guest_id TEXT DEFAULT '',target_tv TEXT NOT NULL DEFAULT 'default',position INTEGER NOT NULL,source TEXT DEFAULT 'request',status TEXT DEFAULT 'queued',party_id INTEGER,playlist_id INTEGER,votes INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,started_at TEXT,finished_at TEXT);
  CREATE TABLE IF NOT EXISTS search_cache(query TEXT PRIMARY KEY,payload TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS playlists(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS playlist_items(id INTEGER PRIMARY KEY AUTOINCREMENT,playlist_id INTEGER NOT NULL,video_id TEXT NOT NULL,title TEXT NOT NULL,channel TEXT DEFAULT '',thumbnail TEXT DEFAULT '',duration_seconds INTEGER DEFAULT 0,enabled INTEGER DEFAULT 1,position INTEGER NOT NULL,added_from TEXT DEFAULT 'manual',created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(playlist_id,video_id),FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE);
  CREATE TABLE IF NOT EXISTS base_play_history(id INTEGER PRIMARY KEY AUTOINCREMENT,target_tv TEXT NOT NULL,playlist_item_id INTEGER NOT NULL,party_id INTEGER,played_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS parties(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,playlist_id INTEGER,allowed_devices TEXT NOT NULL,default_tv TEXT NOT NULL,request_limit INTEGER NOT NULL DEFAULT 3,repeat_window INTEGER NOT NULL DEFAULT 20,queue_locked INTEGER NOT NULL DEFAULT 0,upvote_sort INTEGER NOT NULL DEFAULT 1,detect_external_skip INTEGER NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 0,started_at TEXT DEFAULT CURRENT_TIMESTAMP,ended_at TEXT,FOREIGN KEY(playlist_id) REFERENCES playlists(id));
  CREATE TABLE IF NOT EXISTS votes(queue_id INTEGER NOT NULL,guest_id TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(queue_id,guest_id),FOREIGN KEY(queue_id) REFERENCES queue(id) ON DELETE CASCADE);
  CREATE TABLE IF NOT EXISTS quota_usage(quota_date TEXT PRIMARY KEY,search_api_calls INTEGER DEFAULT 0,search_cache_hits INTEGER DEFAULT 0,search_failures INTEGER DEFAULT 0,quota_exceeded INTEGER DEFAULT 0,playlist_api_calls INTEGER DEFAULT 0,last_search_at TEXT);
  CREATE TABLE IF NOT EXISTS playback_events(id INTEGER PRIMARY KEY AUTOINCREMENT,party_id INTEGER,target_tv TEXT,event TEXT,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  INSERT OR IGNORE INTO playlists(id,name) VALUES(1,'Party allgemein');
  INSERT OR IGNORE INTO settings(key,value) VALUES('playback_enabled','true');
  """)
  for n,typ,default in [('guest_id','TEXT',"''"),('party_id','INTEGER','NULL'),('playlist_id','INTEGER','NULL'),('votes','INTEGER','0')]:
   if not col(c,'queue',n): c.execute(f'ALTER TABLE queue ADD COLUMN {n} {typ} DEFAULT {default}')
  if c.execute('SELECT COUNT(*) n FROM parties').fetchone()['n']==0:
   devices=','.join(d['id'] for d in settings.parsed_devices()); c.execute('INSERT INTO parties(name,playlist_id,allowed_devices,default_tv,request_limit,active) VALUES(?,?,?,?,?,1)',('Standard-Party',1,devices,settings.default_tv,settings.max_requests_per_guest))
  # migrate old base playlist if present
  if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='base_playlist'").fetchone():
   c.execute("INSERT OR IGNORE INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from) SELECT 1,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from FROM base_playlist")
  c.execute('CREATE INDEX IF NOT EXISTS idx_queue_party_tv_status ON queue(party_id,target_tv,status,position)')
def setting(k,d=''):
 with conn() as c:
  r=c.execute('SELECT value FROM settings WHERE key=?',(k,)).fetchone(); return r['value'] if r else d
def set_setting(k,v):
 with conn() as c:c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,str(v)))
