import json,re
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
import httpx
from .config import settings
from .db import conn
V=re.compile(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?v=|shorts/|embed/))([A-Za-z0-9_-]{11})');P=re.compile(r'[?&]list=([A-Za-z0-9_-]+)')
def video_id(x):
 x=x.strip();m=V.search(x);return x if re.fullmatch(r'[A-Za-z0-9_-]{11}',x) else(m.group(1) if m else None)
def playlist_id(x):
 x=x.strip();m=P.search(x);return m.group(1) if m else(x if re.fullmatch(r'[A-Za-z0-9_-]{10,}',x) else None)
def dur(x):
 m=re.fullmatch(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',x or'')
 if not m:return 0
 d,h,mi,s=[int(a or 0) for a in m.groups()];return d*86400+h*3600+mi*60+s
def qdate():return datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
def bump(f):
 with conn() as c:c.execute('INSERT OR IGNORE INTO quota_usage(quota_date) VALUES(?)',(qdate(),));c.execute(f'UPDATE quota_usage SET {f}={f}+1,last_search_at=CURRENT_TIMESTAMP WHERE quota_date=?',(qdate(),))
def quota():
 now=datetime.now(ZoneInfo('America/Los_Angeles'));reset=(now+timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
 with conn() as c:r=c.execute('SELECT * FROM quota_usage WHERE quota_date=?',(qdate(),)).fetchone()
 x=dict(r) if r else {'search_api_calls':0,'search_cache_hits':0,'search_failures':0,'playlist_api_calls':0};x.update({'limit':settings.youtube_search_daily_limit,'warning_at':settings.youtube_search_warning_at,'hard_stop_at':settings.youtube_search_hard_stop_at,'reset_at':reset.astimezone(ZoneInfo(settings.tz)).isoformat()});return x
async def details(ids):
 out=[]
 async with httpx.AsyncClient(timeout=20) as c:
  for i in range(0,len(ids),50):
   r=await c.get('https://www.googleapis.com/youtube/v3/videos',params={'key':settings.youtube_api_key,'part':'snippet,contentDetails,status','id':','.join(ids[i:i+50])});r.raise_for_status()
   for z in r.json().get('items',[]):
    s=z['snippet'];t=s.get('thumbnails',{});out.append({'video_id':z['id'],'title':s['title'],'channel':s['channelTitle'],'thumbnail':t.get('medium',t.get('default',{})).get('url',''),'duration_seconds':dur(z.get('contentDetails',{}).get('duration')),'is_live':s.get('liveBroadcastContent') in ('live','upcoming'),'embeddable':z.get('status',{}).get('embeddable',True)})
 return out
async def search(q):
 n=' '.join(q.lower().split())
 if len(n)<settings.search_min_length:raise ValueError(f'Suche muss mindestens {settings.search_min_length} Zeichen lang sein')
 limit=max(1,min(50,int(settings.search_results)))
 cut=datetime.now(timezone.utc)-timedelta(hours=settings.search_cache_hours)
 with conn() as c:r=c.execute('SELECT * FROM search_cache WHERE query=?',(n,)).fetchone()
 if r and datetime.fromisoformat(r['created_at'].replace(' ','T')).replace(tzinfo=timezone.utc)>=cut:bump('search_cache_hits');return json.loads(r['payload'])[:limit]
 if quota()['search_api_calls']>=settings.youtube_search_hard_stop_at:raise RuntimeError('Lokales YouTube-Suchlimit erreicht')
 bump('search_api_calls')
 try:
  async with httpx.AsyncClient(timeout=20) as c:r=await c.get('https://www.googleapis.com/youtube/v3/search',params={'key':settings.youtube_api_key,'part':'snippet','type':'video','maxResults':limit,'q':q,'safeSearch':'moderate','videoEmbeddable':'true'});r.raise_for_status()
  a=await details([x['id']['videoId'] for x in r.json().get('items',[]) if x.get('id',{}).get('videoId')]);a=[x for x in a if not x['is_live'] and x['embeddable'] and 0<x['duration_seconds']<=settings.max_video_minutes*60]
  with conn() as c:c.execute('INSERT INTO search_cache VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(query) DO UPDATE SET payload=excluded.payload,created_at=CURRENT_TIMESTAMP',(n,json.dumps(a)))
  return a[:limit]
 except:bump('search_failures');raise
async def playlist(x):
 pid=playlist_id(x)
 if not pid:raise ValueError('Ungültige Playlist-URL')
 ids=[];token=None
 async with httpx.AsyncClient(timeout=20) as c:
  while True:
   p={'key':settings.youtube_api_key,'part':'contentDetails','playlistId':pid,'maxResults':50};p.update({'pageToken':token} if token else{});bump('playlist_api_calls');r=await c.get('https://www.googleapis.com/youtube/v3/playlistItems',params=p);r.raise_for_status();b=r.json();ids += [i['contentDetails']['videoId'] for i in b.get('items',[])];token=b.get('nextPageToken')
   if not token:break
 return await details(ids)
