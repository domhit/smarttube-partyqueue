import json, re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import httpx
from .config import settings
from .db import conn

VIDEO_RE = re.compile(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?v=|shorts/|embed/))([A-Za-z0-9_-]{11})')
PLAYLIST_RE = re.compile(r'[?&]list=([A-Za-z0-9_-]+)')

def parse_video_id(value):
    value = value.strip()
    match = VIDEO_RE.search(value)
    return value if re.fullmatch(r'[A-Za-z0-9_-]{11}', value) else (match.group(1) if match else None)

def parse_playlist_id(value):
    value = value.strip()
    match = PLAYLIST_RE.search(value)
    return match.group(1) if match else (value if re.fullmatch(r'[A-Za-z0-9_-]{10,}', value) else None)

def iso_seconds(value):
    match = re.fullmatch(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', value or '')
    if not match:
        return 0
    d, h, m, s = [int(x or 0) for x in match.groups()]
    return d * 86400 + h * 3600 + m * 60 + s

def quota_date():
    return datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()

def bump(field, count=1):
    allowed = {'search_api_calls', 'search_cache_hits', 'search_failures', 'quota_exceeded', 'playlist_api_calls'}
    if field not in allowed:
        raise ValueError('Ungültiges Quota-Feld')
    with conn() as c:
        c.execute('INSERT OR IGNORE INTO quota_usage(quota_date) VALUES(?)', (quota_date(),))
        c.execute(f'UPDATE quota_usage SET {field}={field}+?,last_search_at=CURRENT_TIMESTAMP WHERE quota_date=?', (count, quota_date()))

def quota_status():
    now = datetime.now(ZoneInfo('America/Los_Angeles'))
    reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    with conn() as c:
        row = c.execute('SELECT * FROM quota_usage WHERE quota_date=?', (quota_date(),)).fetchone()
    data = dict(row) if row else {'quota_date': quota_date(), 'search_api_calls': 0, 'search_cache_hits': 0, 'search_failures': 0, 'quota_exceeded': 0, 'playlist_api_calls': 0, 'last_search_at': None}
    data.update({'limit': settings.youtube_search_daily_limit, 'warning_at': settings.youtube_search_warning_at, 'hard_stop_at': settings.youtube_search_hard_stop_at, 'reset_at': reset.astimezone(ZoneInfo(settings.tz)).isoformat()})
    return data

async def video_details(ids):
    if not settings.youtube_api_key:
        raise RuntimeError('YOUTUBE_API_KEY fehlt')
    if not ids:
        return []
    result = []
    async with httpx.AsyncClient(timeout=20) as client:
        for start in range(0, len(ids), 50):
            response = await client.get('https://www.googleapis.com/youtube/v3/videos', params={'key': settings.youtube_api_key, 'part': 'snippet,contentDetails,status', 'id': ','.join(ids[start:start + 50])})
            response.raise_for_status()
            for item in response.json().get('items', []):
                sn = item['snippet']; thumbs = sn.get('thumbnails', {})
                result.append({'video_id': item['id'], 'title': sn['title'], 'channel': sn['channelTitle'], 'thumbnail': thumbs.get('medium', thumbs.get('default', {})).get('url', ''), 'duration_seconds': iso_seconds(item.get('contentDetails', {}).get('duration')), 'is_live': sn.get('liveBroadcastContent') in ('live', 'upcoming'), 'embeddable': item.get('status', {}).get('embeddable', True)})
    return result

async def search_youtube(query):
    normalized = ' '.join(query.strip().lower().split())
    if len(normalized) < settings.search_min_length:
        raise ValueError(f'Mindestens {settings.search_min_length} Zeichen')
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.search_cache_hours)
    with conn() as c:
        row = c.execute('SELECT payload,created_at FROM search_cache WHERE query=?', (normalized,)).fetchone()
    if row:
        try:
            created = datetime.fromisoformat(row['created_at'].replace(' ', 'T')).replace(tzinfo=timezone.utc)
            if created >= cutoff:
                bump('search_cache_hits')
                return json.loads(row['payload'])
        except ValueError:
            pass
    if quota_status()['search_api_calls'] >= settings.youtube_search_hard_stop_at:
        bump('quota_exceeded')
        raise RuntimeError('Lokales YouTube-Suchlimit erreicht. Linkeingabe bleibt verfügbar.')
    bump('search_api_calls')
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get('https://www.googleapis.com/youtube/v3/search', params={'key': settings.youtube_api_key, 'part': 'snippet', 'type': 'video', 'maxResults': min(settings.search_results, 50), 'q': query, 'safeSearch': 'moderate', 'videoEmbeddable': 'true'})
            response.raise_for_status()
        ids = [x['id']['videoId'] for x in response.json().get('items', []) if x.get('id', {}).get('videoId')]
        result = await video_details(ids)
        result = [x for x in result if not x['is_live'] and x['embeddable'] and 0 < x['duration_seconds'] <= settings.max_video_minutes * 60]
        with conn() as c:
            c.execute('INSERT INTO search_cache(query,payload,created_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(query) DO UPDATE SET payload=excluded.payload,created_at=CURRENT_TIMESTAMP', (normalized, json.dumps(result)))
        return result
    except Exception:
        bump('search_failures')
        raise

async def playlist_items(value):
    playlist_id = parse_playlist_id(value)
    if not playlist_id:
        raise ValueError('Ungültige Playlist-URL oder ID')
    ids, page_token = [], None
    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            params = {'key': settings.youtube_api_key, 'part': 'contentDetails', 'playlistId': playlist_id, 'maxResults': 50}
            if page_token:
                params['pageToken'] = page_token
            bump('playlist_api_calls')
            response = await client.get('https://www.googleapis.com/youtube/v3/playlistItems', params=params)
            response.raise_for_status()
            body = response.json()
            ids.extend(x['contentDetails']['videoId'] for x in body.get('items', []) if x.get('contentDetails', {}).get('videoId'))
            page_token = body.get('nextPageToken')
            if not page_token:
                break
    return await video_details(ids)
