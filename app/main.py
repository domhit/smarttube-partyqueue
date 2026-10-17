import asyncio, secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .config import settings
from .db import init_db, conn, setting, set_setting
from .youtube import search_youtube, video_details, parse_video_id

clients = set()
play_locks: dict[str, asyncio.Lock] = {}
DEVICES = settings.parsed_devices()
DEVICE_IDS = {d['id'] for d in DEVICES}

class AddItem(BaseModel):
    video_id: Optional[str] = None
    url: Optional[str] = None
    requested_by: str = 'Gast'
    target_tv: Optional[str] = None

class AdminAuth(BaseModel):
    password: str

class Reorder(BaseModel):
    ids: list[int]
    target_tv: str

class PlaybackEnd(BaseModel):
    target_tv: str

async def snapshot():
    with conn() as c:
        queued = [dict(r) for r in c.execute("SELECT * FROM queue WHERE status='queued' ORDER BY target_tv,position,id")]
        current = [dict(r) for r in c.execute("SELECT * FROM queue WHERE status='playing' ORDER BY target_tv,started_at DESC")]
        history = [dict(r) for r in c.execute("SELECT * FROM queue WHERE status IN ('played','skipped') ORDER BY finished_at DESC LIMIT 60")]
    return {
        'devices': DEVICES,
        'default_tv': settings.default_tv,
        'queue': queued,
        'current': {x['target_tv']: x for x in current},
        'history': history,
        'locked': setting('queue_locked', 'false') == 'true',
        'playback_enabled': setting('playback_enabled', 'true') == 'true'
    }

async def broadcast():
    data = await snapshot()
    dead = []
    for ws in clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)

def admin_ok(password):
    return secrets.compare_digest(password or '', settings.admin_password)

def valid_tv(target_tv: Optional[str]) -> str:
    tv = target_tv or settings.default_tv
    if tv not in DEVICE_IDS:
        raise HTTPException(400, f'Unbekanntes TV-Gerät: {tv}')
    return tv

async def ha_play(item):
    endpoint = f"{settings.ha_url.rstrip('/')}/api/webhook/{settings.ha_webhook_id}"
    payload = {
        'url': f"https://www.youtube.com/watch?v={item['video_id']}",
        'video_id': item['video_id'],
        'queue_item_id': item['id'],
        'target_tv': item['target_tv'],
        'smarttube_package': settings.smarttube_package
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(endpoint, json=payload)
        r.raise_for_status()

async def start_next(target_tv: str):
    target_tv = valid_tv(target_tv)
    lock = play_locks.setdefault(target_tv, asyncio.Lock())
    async with lock:
        if setting('playback_enabled', 'true') != 'true':
            return
        with conn() as c:
            playing = c.execute("SELECT id FROM queue WHERE status='playing' AND target_tv=? LIMIT 1", (target_tv,)).fetchone()
            if playing:
                return
            row = c.execute("SELECT * FROM queue WHERE status='queued' AND target_tv=? ORDER BY position,id LIMIT 1", (target_tv,)).fetchone()
            if not row:
                return
            item = dict(row)
            c.execute("UPDATE queue SET status='playing',started_at=CURRENT_TIMESTAMP WHERE id=?", (item['id'],))
        try:
            await ha_play(item)
        except Exception:
            with conn() as c:
                c.execute("UPDATE queue SET status='queued',started_at=NULL WHERE id=?", (item['id'],))
            raise
        await broadcast()

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title='SmartTube PartyQueue V2', version='2.1.0', lifespan=lifespan)
BASE = Path(__file__).parent
app.mount('/static', StaticFiles(directory=BASE/'static'), name='static')

@app.get('/')
async def guest(): return FileResponse(BASE/'static/guest.html')

@app.get('/host')
async def host(): return FileResponse(BASE/'static/host.html')

@app.get('/api/health')
async def health(): return {'ok': True, 'version': '2.1.0', 'devices': DEVICES}

@app.get('/api/state')
async def state(): return await snapshot()

@app.get('/api/search')
async def search(q: str):
    try:
        return await search_youtube(q)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, e.response.text[:500])

@app.post('/api/queue')
async def add(item: AddItem):
    if setting('queue_locked', 'false') == 'true':
        raise HTTPException(423, 'Queue ist gesperrt')
    target_tv = valid_tv(item.target_tv)
    vid = item.video_id or parse_video_id(item.url or '')
    if not vid:
        raise HTTPException(400, 'Ungültige YouTube-URL oder Video-ID')
    details = await video_details([vid])
    if not details:
        raise HTTPException(404, 'Video nicht gefunden oder nicht verfügbar')
    d = details[0]
    if d['is_live']:
        raise HTTPException(400, 'Livestreams sind nicht erlaubt')
    if d['duration_seconds'] > settings.max_video_minutes * 60:
        raise HTTPException(400, f'Video länger als {settings.max_video_minutes} Minuten')
    guest = (item.requested_by.strip() or 'Gast')[:40]
    with conn() as c:
        if c.execute("SELECT 1 FROM queue WHERE video_id=? AND target_tv=? AND status IN ('queued','playing')", (vid, target_tv)).fetchone():
            raise HTTPException(409, 'Titel ist auf diesem TV bereits eingeplant')
        count = c.execute("SELECT COUNT(*) n FROM queue WHERE requested_by=? AND target_tv=? AND status='queued'", (guest, target_tv)).fetchone()['n']
        if count >= settings.max_requests_per_guest:
            raise HTTPException(429, f'Maximal {settings.max_requests_per_guest} offene Wünsche pro Gast und TV')
        pos = c.execute("SELECT COALESCE(MAX(position),0)+1 n FROM queue WHERE target_tv=? AND status='queued'", (target_tv,)).fetchone()['n']
        cur = c.execute('INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,target_tv,position) VALUES(?,?,?,?,?,?,?,?)',
            (vid, d['title'], d['channel'], d['thumbnail'], d['duration_seconds'], guest, target_tv, pos))
        inserted = cur.lastrowid
    await broadcast()
    await start_next(target_tv)
    return {'ok': True, 'id': inserted, 'target_tv': target_tv}

@app.post('/api/playback/end')
async def playback_end(body: PlaybackEnd, x_admin_password: str = Header(default='')):
    if not admin_ok(x_admin_password):
        raise HTTPException(401, 'Nicht autorisiert')
    target_tv = valid_tv(body.target_tv)
    with conn() as c:
        c.execute("UPDATE queue SET status='played',finished_at=CURRENT_TIMESTAMP WHERE status='playing' AND target_tv=?", (target_tv,))
    await broadcast()
    await start_next(target_tv)
    return {'ok': True, 'target_tv': target_tv}

@app.post('/api/admin/login')
async def login(a: AdminAuth):
    if not admin_ok(a.password): raise HTTPException(401, 'Falsches Passwort')
    return {'ok': True}

@app.post('/api/admin/reorder')
async def reorder(x: Reorder, x_admin_password: str = Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401, 'Nicht autorisiert')
    target_tv = valid_tv(x.target_tv)
    with conn() as c:
        for pos, item_id in enumerate(x.ids, 1):
            c.execute("UPDATE queue SET position=? WHERE id=? AND target_tv=? AND status='queued'", (pos, item_id, target_tv))
    await broadcast()
    return {'ok': True}

@app.post('/api/admin/skip')
async def skip(body: PlaybackEnd, x_admin_password: str = Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401, 'Nicht autorisiert')
    target_tv = valid_tv(body.target_tv)
    with conn() as c:
        c.execute("UPDATE queue SET status='skipped',finished_at=CURRENT_TIMESTAMP WHERE status='playing' AND target_tv=?", (target_tv,))
    await broadcast()
    await start_next(target_tv)
    return {'ok': True}

@app.delete('/api/admin/queue/{item_id}')
async def delete(item_id: int, x_admin_password: str = Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401, 'Nicht autorisiert')
    with conn() as c:
        c.execute("DELETE FROM queue WHERE id=? AND status='queued'", (item_id,))
    await broadcast()
    return {'ok': True}

@app.post('/api/admin/lock')
async def lock(a: AdminAuth):
    if not admin_ok(a.password): raise HTTPException(401, 'Nicht autorisiert')
    new = 'false' if setting('queue_locked', 'false') == 'true' else 'true'
    set_setting('queue_locked', new)
    await broadcast()
    return {'locked': new == 'true'}

@app.websocket('/ws')
async def ws(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    await websocket.send_json(await snapshot())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.discard(websocket)
