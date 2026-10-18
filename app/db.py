import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import settings
DB=Path(settings.data_dir)/'partyqueue.db'
@contextmanager
def conn():
 DB.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA foreign_keys=ON')
 try:yield c;c.commit()
 finally:c.close()
def col(c,t,n):return any(r['name']==n for r in c.execute(f'PRAGMA table_info({t})'))
def init_db():
 with conn() as c:
  c.executescript("""
  CREATE TABLE IF NOT EXISTS queue(id INTEGER PRIMARY KEY AUTOINCREMENT,video_id TEXT NOT NULL,title TEXT NOT NULL,channel TEXT DEFAULT '',thumbnail TEXT DEFAULT '',duration_seconds INTEGER DEFAULT 0,requested_by TEXT DEFAULT 'Gast',guest_id TEXT DEFAULT '',target_tv TEXT NOT NULL,position INTEGER NOT NULL,source TEXT DEFAULT 'request',status TEXT DEFAULT 'queued',party_id INTEGER,playlist_id INTEGER,votes INTEGER DEFAULT 0,admin_priority INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,started_at TEXT,finished_at TEXT);
  CREATE TABLE IF NOT EXISTS search_cache(query TEXT PRIMARY KEY,payload TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS playlists(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS playlist_items(id INTEGER PRIMARY KEY AUTOINCREMENT,playlist_id INTEGER NOT NULL,video_id TEXT NOT NULL,title TEXT NOT NULL,channel TEXT DEFAULT '',thumbnail TEXT DEFAULT '',duration_seconds INTEGER DEFAULT 0,enabled INTEGER DEFAULT 1,position INTEGER NOT NULL,added_from TEXT DEFAULT 'manual',created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(playlist_id,video_id),FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE);
  CREATE TABLE IF NOT EXISTS base_play_history(id INTEGER PRIMARY KEY AUTOINCREMENT,target_tv TEXT NOT NULL,playlist_item_id INTEGER NOT NULL,party_id INTEGER,played_at TEXT DEFAULT CURRENT_TIMESTAMP);
  CREATE TABLE IF NOT EXISTS parties(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,playlist_id INTEGER,allowed_devices TEXT NOT NULL,default_tv TEXT NOT NULL,request_limit INTEGER DEFAULT 3,repeat_window INTEGER DEFAULT 20,queue_locked INTEGER DEFAULT 0,upvote_sort INTEGER DEFAULT 1,detect_external_skip INTEGER DEFAULT 0,playlist_enabled INTEGER DEFAULT 1,active INTEGER DEFAULT 0,started_at TEXT DEFAULT CURRENT_TIMESTAMP,ended_at TEXT);
  CREATE TABLE IF NOT EXISTS votes(queue_id INTEGER,guest_id TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(queue_id,guest_id));
  CREATE TABLE IF NOT EXISTS quota_usage(quota_date TEXT PRIMARY KEY,search_api_calls INTEGER DEFAULT 0,search_cache_hits INTEGER DEFAULT 0,search_failures INTEGER DEFAULT 0,quota_exceeded INTEGER DEFAULT 0,playlist_api_calls INTEGER DEFAULT 0,last_search_at TEXT);
  CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
  INSERT OR IGNORE INTO playlists(id,name) VALUES(1,'Party allgemein');
  """)
  for n,t,d in [('guest_id','TEXT',"''"),('party_id','INTEGER','NULL'),('playlist_id','INTEGER','NULL'),('votes','INTEGER','0'),('admin_priority','INTEGER','0')]:
   if not col(c,'queue',n):c.execute(f'ALTER TABLE queue ADD COLUMN {n} {t} DEFAULT {d}')
  if not col(c,'parties','playlist_enabled'):c.execute('ALTER TABLE parties ADD COLUMN playlist_enabled INTEGER DEFAULT 1')
  if col(c,'base_play_history','base_item_id'):
   hp=col(c,'base_play_history','party_id');c.execute('CREATE TABLE IF NOT EXISTS base_play_history_new(id INTEGER PRIMARY KEY AUTOINCREMENT,target_tv TEXT NOT NULL,playlist_item_id INTEGER NOT NULL,party_id INTEGER,played_at TEXT DEFAULT CURRENT_TIMESTAMP)');pe='party_id' if hp else 'NULL';c.execute(f'INSERT OR IGNORE INTO base_play_history_new(id,target_tv,playlist_item_id,party_id,played_at) SELECT id,target_tv,base_item_id,{pe},played_at FROM base_play_history');c.execute('DROP TABLE base_play_history');c.execute('ALTER TABLE base_play_history_new RENAME TO base_play_history')
  if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='base_playlist'").fetchone():c.execute("INSERT OR IGNORE INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from) SELECT 1,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from FROM base_playlist")
  if c.execute('SELECT COUNT(*) n FROM parties').fetchone()['n']==0:c.execute('INSERT INTO parties(name,playlist_id,allowed_devices,default_tv,request_limit,active) VALUES(?,?,?,?,?,1)',('Standard-Party',1,','.join(d['id'] for d in settings.parsed_devices()),settings.default_tv,settings.max_requests_per_guest))
