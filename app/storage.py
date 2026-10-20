from .db import conn

SETTING_TYPES={
 "max_video_minutes":int,"max_requests_per_guest":int,"search_cache_hours":int,"search_min_length":int,"search_results":int,
 "youtube_search_daily_limit":int,"youtube_search_warning_at":int,"youtube_search_hard_stop_at":int,"base_playlist_recent_exclude":int,
 "prestart_seconds":float,"idle_fallback_delay":float,"prestart_idle_guard":float,"external_skip_min_previous":float,
 "external_skip_max_new":float,"play_confirm_timeout":float,"play_retry_timeout":float,"play_webhook_timeout":float,
 "play_confirm_max_position":float,"smarttube_package":str,"youtube_api_key":str,"ha_url":str,"ha_webhook_id":str,"tz":str
}

def list_tvs(enabled_only=False):
 q="SELECT * FROM tvs"+(" WHERE enabled=1" if enabled_only else "")+" ORDER BY is_default DESC,name COLLATE NOCASE,id"
 with conn() as c:return [dict(r) for r in c.execute(q)]

def get_tv(tv_id):
 with conn() as c:
  r=c.execute("SELECT * FROM tvs WHERE id=?",(tv_id,)).fetchone();return dict(r) if r else None

def save_tv(data,old_id=None):
 tv_id=data["id"].strip();name=data["name"].strip()
 if not tv_id or not re_id(tv_id):raise ValueError("TV-ID darf nur Buchstaben, Zahlen, Punkt, Minus und Unterstrich enthalten")
 if not name:raise ValueError("TV-Name fehlt")
 old_id=old_id or tv_id
 with conn() as c:
  if old_id!=tv_id and c.execute("SELECT 1 FROM tvs WHERE id=?",(tv_id,)).fetchone():raise ValueError("TV-ID existiert bereits")
  exists=c.execute("SELECT 1 FROM tvs WHERE id=?",(old_id,)).fetchone()
  values=(tv_id,name,data.get("host",data.get("ip_address","")).strip(),int(data.get("enabled",True)),int(data.get("is_default",False)),data.get("ha_entity","").strip(),"")
  if exists:
   c.execute("UPDATE tvs SET id=?,name=?,ip_address=?,enabled=?,is_default=?,ha_entity=?,adb_serial=? WHERE id=?",values+(old_id,))
   if old_id!=tv_id:
    c.execute("UPDATE parties SET default_tv=? WHERE default_tv=?",(tv_id,old_id))
  else:c.execute("INSERT INTO tvs(id,name,ip_address,enabled,is_default,ha_entity,adb_serial) VALUES(?,?,?,?,?,?,?)",values)
  if data.get("is_default"):
   c.execute("UPDATE tvs SET is_default=CASE WHEN id=? THEN 1 ELSE 0 END",(tv_id,))
 return get_tv(tv_id)

def re_id(value):
 import re
 return bool(re.fullmatch(r"[A-Za-z0-9_.-]+",value))

def delete_tv(tv_id):
 with conn() as c:
  if c.execute("SELECT 1 FROM parties WHERE active=1 AND (default_tv=? OR ','||allowed_devices||',' LIKE ?)",(tv_id,f"%,{tv_id},%" )).fetchone():raise ValueError("TV wird von der aktiven Party verwendet")
  if c.execute("SELECT COUNT(*) n FROM tvs").fetchone()["n"]<=1:raise ValueError("Der letzte TV kann nicht gelöscht werden")
  c.execute("DELETE FROM tvs WHERE id=?",(tv_id,))
  if not c.execute("SELECT 1 FROM tvs WHERE is_default=1").fetchone():c.execute("UPDATE tvs SET is_default=1 WHERE id=(SELECT id FROM tvs ORDER BY name LIMIT 1)")

def default_tv():
 with conn() as c:
  r=c.execute("SELECT id FROM tvs WHERE enabled=1 ORDER BY is_default DESC,name LIMIT 1").fetchone();return r["id"] if r else None

def all_settings():
 with conn() as c:raw={r["key"]:r["value"] for r in c.execute("SELECT key,value FROM settings_store")}
 out={}
 for k,t in SETTING_TYPES.items():
  if k not in raw:continue
  try:out[k]=t(raw[k])
  except:out[k]=raw[k]
 return out

def set_settings(values):
 unknown=set(values)-set(SETTING_TYPES)
 if unknown:raise ValueError("Unbekannte Einstellung: "+", ".join(sorted(unknown)))
 with conn() as c:
  for k,v in values.items():
   cast=SETTING_TYPES[k];value=cast(v)
   if cast in (int,float) and value<0:raise ValueError(f"{k} darf nicht negativ sein")
   c.execute("INSERT INTO settings_store(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(k,str(value)))
 return all_settings()

def apply_runtime_settings(settings):
 for k,v in all_settings().items():setattr(settings,k,v)


def set_default_tv(tv_id):
 with conn() as c:
  if not c.execute("SELECT 1 FROM tvs WHERE id=? AND enabled=1",(tv_id,)).fetchone():raise ValueError("Nur ein aktiver TV kann Standardgerät sein")
  c.execute("UPDATE tvs SET is_default=CASE WHEN id=? THEN 1 ELSE 0 END",(tv_id,))
 return get_tv(tv_id)

def set_tv_enabled(tv_id,enabled):
 with conn() as c:
  row=c.execute("SELECT is_default FROM tvs WHERE id=?",(tv_id,)).fetchone()
  if not row:raise ValueError("TV nicht gefunden")
  if row["is_default"] and not enabled:raise ValueError("Standardgerät kann nicht deaktiviert werden")
  c.execute("UPDATE tvs SET enabled=? WHERE id=?",(int(enabled),tv_id))
 return get_tv(tv_id)
