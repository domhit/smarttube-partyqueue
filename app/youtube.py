import json, re
from datetime import datetime, timezone, timedelta
import httpx
from .config import settings
from .db import conn

VIDEO_RE=re.compile(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?v=|shorts/|embed/))([A-Za-z0-9_-]{11})')

def parse_video_id(value: str):
    value=value.strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', value): return value
    m=VIDEO_RE.search(value)
    return m.group(1) if m else None

def iso_duration_seconds(value):
    m=re.fullmatch(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', value or '')
    if not m: return 0
    d,h,mi,s=[int(x or 0) for x in m.groups()]
    return d*86400+h*3600+mi*60+s

async def video_details(ids):
    if not settings.youtube_api_key: raise RuntimeError('YOUTUBE_API_KEY fehlt')
    if not ids: return []
    params={'key':settings.youtube_api_key,'part':'snippet,contentDetails,status,liveStreamingDetails','id':','.join(ids)}
    async with httpx.AsyncClient(timeout=15) as client:
        r=await client.get('https://www.googleapis.com/youtube/v3/videos',params=params); r.raise_for_status()
    out=[]
    for item in r.json().get('items',[]): 
        sn=item['snippet']; dur=iso_duration_seconds(item.get('contentDetails',{}).get('duration'))
        out.append({'video_id':item['id'],'title':sn['title'],'channel':sn['channelTitle'],
          'thumbnail':sn.get('thumbnails',{}).get('medium',sn.get('thumbnails',{}).get('default',{})).get('url',''),
          'duration_seconds':dur,'is_live':sn.get('liveBroadcastContent') in ('live','upcoming'),
          'embeddable':item.get('status',{}).get('embeddable',True)})
    return out

async def search_youtube(query):
    q=' '.join(query.strip().lower().split())
    if len(q)<settings.search_min_length: raise ValueError(f'Mindestens {settings.search_min_length} Zeichen')
    cutoff=datetime.now(timezone.utc)-timedelta(hours=settings.search_cache_hours)
    with conn() as c:
        row=c.execute('SELECT payload,created_at FROM search_cache WHERE query=?',(q,)).fetchone()
        if row:
            try:
                created=datetime.fromisoformat(row['created_at'].replace(' ','T')).replace(tzinfo=timezone.utc)
                if created>=cutoff: return json.loads(row['payload'])
            except ValueError: pass
    if not settings.youtube_api_key: raise RuntimeError('YOUTUBE_API_KEY fehlt')
    params={'key':settings.youtube_api_key,'part':'snippet','type':'video','maxResults':settings.search_results,
      'q':query,'safeSearch':'moderate','videoEmbeddable':'true'}
    async with httpx.AsyncClient(timeout=15) as client:
        r=await client.get('https://www.googleapis.com/youtube/v3/search',params=params); r.raise_for_status()
    ids=[x['id']['videoId'] for x in r.json().get('items',[]) if x.get('id',{}).get('videoId')]
    result=await video_details(ids)
    result=[x for x in result if not x['is_live'] and x['embeddable'] and 0<x['duration_seconds']<=settings.max_video_minutes*60]
    with conn() as c:
        c.execute('INSERT INTO search_cache(query,payload,created_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(query) DO UPDATE SET payload=excluded.payload,created_at=CURRENT_TIMESTAMP',(q,json.dumps(result)))
    return result
