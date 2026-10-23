from .db import conn
SETTING_TYPES={"max_video_minutes":int,"max_requests_per_guest":int,"search_cache_hours":int,"search_min_length":int,"search_results":int,"youtube_search_daily_limit":int,"youtube_search_warning_at":int,"youtube_search_hard_stop_at":int,"base_playlist_recent_exclude":int,"prestart_seconds":float,"idle_fallback_delay":float,"prestart_idle_guard":float,"external_skip_min_previous":float,"external_skip_max_new":float,"play_confirm_timeout":float,"play_retry_timeout":float,"play_confirm_max_position":float,"rest_poll_interval":float,"queue_prefetch_interval":float,"adb_bootstrap_enabled":int,"adb_bootstrap_port":int,"adb_bootstrap_grace":float,"adb_bootstrap_ready_timeout":float,"adb_bootstrap_cooldown":float,"smarttube_package":str,"sync_drift_tolerance":float,"sync_resume_margin":float,"sync_seek_threshold":float,"youtube_api_key":str,"tz":str}
def list_tvs(enabled_only=False):
 with conn() as c:return [dict(r) for r in c.execute("SELECT * FROM tvs"+(" WHERE enabled=1" if enabled_only else "")+" ORDER BY name COLLATE NOCASE,id")]
def get_tv(i):
 with conn() as c:
  r=c.execute('SELECT * FROM tvs WHERE id=?',(i,)).fetchone();return dict(r) if r else None
def save_tv(d,old_id=None):
 import re
 i=d['id'].strip();n=d['name'].strip();h=d.get('host',d.get('ip_address','')).strip();port=int(d.get('api_port',8090));u=d.get('api_username','admin').strip() or 'admin';pw=d.get('api_password','')
 if not re.fullmatch(r'[A-Za-z0-9_.-]+',i):raise ValueError('Ungültige TV-ID')
 if not n or not h:raise ValueError('Name und Host sind erforderlich')
 if not 1<=port<=65535:raise ValueError('API-Port ist ungültig')
 old_id=old_id or i;vals=(i,n,h,port,u,pw,int(d.get('enabled',True)),int(d.get('is_default',False)))
 with conn() as c:
  if c.execute('SELECT 1 FROM tvs WHERE id=?',(old_id,)).fetchone():c.execute('UPDATE tvs SET id=?,name=?,ip_address=?,api_port=?,api_username=?,api_password=?,enabled=?,is_default=? WHERE id=?',vals+(old_id,))
  else:c.execute('INSERT INTO tvs(id,name,ip_address,api_port,api_username,api_password,enabled,is_default) VALUES(?,?,?,?,?,?,?,?)',vals)
  if d.get('is_default'):c.execute('UPDATE tvs SET is_default=CASE WHEN id=? THEN 1 ELSE 0 END',(i,))
 return get_tv(i)
def delete_tv(i):
 with conn() as c:
  if c.execute("SELECT 1 FROM parties WHERE active=1 AND (default_tv=? OR ','||allowed_devices||',' LIKE ?)",(i,f'%,{i},%')).fetchone():raise ValueError('TV wird von der aktiven Party verwendet')
  if c.execute('SELECT COUNT(*) n FROM tvs').fetchone()['n']<=1:raise ValueError('Der letzte TV kann nicht gelöscht werden')
  c.execute('DELETE FROM tvs WHERE id=?',(i,))
def default_tv():
 with conn() as c:
  r=c.execute('SELECT id FROM tvs WHERE enabled=1 ORDER BY is_default DESC,name LIMIT 1').fetchone();return r['id'] if r else None
def all_settings():
 with conn() as c:raw={r['key']:r['value'] for r in c.execute('SELECT key,value FROM settings_store')}
 out={}
 for k,t in SETTING_TYPES.items():
  if k in raw:
   try:out[k]=t(raw[k])
   except:out[k]=raw[k]
 return out
def set_settings(v):

   # Altlasten aus früheren Versionen ignorieren
   v = {
      k: x
      for k, x in v.items()
      if k in SETTING_TYPES
   }

   with conn() as c:
      for k, x in v.items():
         c.execute(
            'INSERT INTO settings_store(key,value) VALUES(?,?) '
            'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
            (k, str(SETTING_TYPES[k](x)))
         )

   return all_settings()
def apply_runtime_settings(s):
 for k,v in all_settings().items():setattr(s,k,v)
def set_default_tv(i):
 with conn() as c:c.execute('UPDATE tvs SET is_default=CASE WHEN id=? THEN 1 ELSE 0 END',(i,))
 return get_tv(i)
def set_tv_enabled(i,e):
 with conn() as c:c.execute('UPDATE tvs SET enabled=? WHERE id=?',(int(e),i))
 return get_tv(i)
