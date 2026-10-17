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

clients=set()
play_lock=asyncio.Lock()

class AddItem(BaseModel):
    video_id: Optional[str]=None
    url: Optional[str]=None
    requested_by: str='Gast'

class AdminAuth(BaseModel): password: str
class Reorder(BaseModel): ids: list[int]
class PlaybackState(BaseModel): state: str='unknown'; position: float=0; duration: float=0; title: str=''

async def snapshot():
    with conn() as c:
        queued=[dict(r) for r in c.execute("SELECT * FROM queue WHERE status='queued' ORDER BY position,id")]
        current=c.execute("SELECT * FROM queue WHERE status='playing' ORDER BY started_at DESC LIMIT 1").fetchone()
        history=[dict(r) for r in c.execute("SELECT * FROM queue WHERE status IN ('played','skipped') ORDER BY finished_at DESC LIMIT 30")]
    return {'queue':queued,'current':dict(current) if current else None,'history':history,
      'locked':setting('queue_locked','false')=='true','playback_enabled':setting('playback_enabled','true')=='true'}

async def broadcast():
    data=await snapshot()
    dead=[]
    for ws in clients:
        try: await ws.send_json(data)
        except Exception: dead.append(ws)
    for ws in dead: clients.discard(ws)

def admin_ok(password): return secrets.compare_digest(password or '',settings.admin_password)

async def ha_play(item):
    url=f"https://www.youtube.com/watch?v={item['video_id']}"
    endpoint=f"{settings.ha_url.rstrip('/')}/api/webhook/{settings.ha_webhook_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        r=await client.post(endpoint,json={'url':url,'video_id':item['video_id'],'queue_item_id':item['id']})
        r.raise_for_status()

async def start_next():
    async with play_lock:
        if setting('playback_enabled','true')!='true': return
        with conn() as c:
            playing=c.execute("SELECT id FROM queue WHERE status='playing' LIMIT 1").fetchone()
            if playing: return
            row=c.execute("SELECT * FROM queue WHERE status='queued' ORDER BY position,id LIMIT 1").fetchone()
            if not row: return
            item=dict(row)
            c.execute("UPDATE queue SET status='playing',started_at=CURRENT_TIMESTAMP WHERE id=?",(item['id'],))
        try: await ha_play(item)
        except Exception:
            with conn() as c: c.execute("UPDATE queue SET status='queued',started_at=NULL WHERE id=?",(item['id'],))
            raise
        await broadcast()

@asynccontextmanager
async def lifespan(app):
    init_db(); yield

app=FastAPI(title='SmartTube PartyQueue V2',version='2.0.0',lifespan=lifespan)
BASE=Path(__file__).parent
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')

@app.get('/')
async def guest(): return FileResponse(BASE/'static/guest.html')
@app.get('/host')
async def host(): return FileResponse(BASE/'static/host.html')
@app.get('/api/health')
async def health(): return {'ok':True,'version':'2.0.0'}
@app.get('/api/state')
async def state(): return await snapshot()
@app.get('/api/search')
async def search(q:str):
    try: return await search_youtube(q)
    except (ValueError,RuntimeError) as e: raise HTTPException(400,str(e))
    except httpx.HTTPStatusError as e: raise HTTPException(502,e.response.text[:500])

@app.post('/api/queue')
async def add(item:AddItem):
    if setting('queue_locked','false')=='true': raise HTTPException(423,'Queue ist gesperrt')
    vid=item.video_id or parse_video_id(item.url or '')
    if not vid: raise HTTPException(400,'Ungültige YouTube-URL oder Video-ID')
    details=await video_details([vid])
    if not details: raise HTTPException(404,'Video nicht gefunden oder nicht verfügbar')
    d=details[0]
    if d['is_live']: raise HTTPException(400,'Livestreams sind nicht erlaubt')
    if d['duration_seconds']>settings.max_video_minutes*60: raise HTTPException(400,f'Video länger als {settings.max_video_minutes} Minuten')
    guest=(item.requested_by.strip() or 'Gast')[:40]
    with conn() as c:
        if c.execute("SELECT 1 FROM queue WHERE video_id=? AND status IN ('queued','playing')",(vid,)).fetchone(): raise HTTPException(409,'Titel ist bereits eingeplant')
        count=c.execute("SELECT COUNT(*) n FROM queue WHERE requested_by=? AND status='queued'",(guest,)).fetchone()['n']
        if count>=settings.max_requests_per_guest: raise HTTPException(429,f'Maximal {settings.max_requests_per_guest} offene Wünsche pro Gast')
        pos=c.execute("SELECT COALESCE(MAX(position),0)+1 n FROM queue WHERE status='queued'").fetchone()['n']
        cur=c.execute('INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,position) VALUES(?,?,?,?,?,?,?)',
          (vid,d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],guest,pos))
        inserted=cur.lastrowid
    await broadcast(); await start_next()
    return {'ok':True,'id':inserted}

@app.post('/api/playback/end')
async def playback_end(x_admin_password:str=Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401,'Nicht autorisiert')
    with conn() as c: c.execute("UPDATE queue SET status='played',finished_at=CURRENT_TIMESTAMP WHERE status='playing'")
    await broadcast(); await start_next(); return {'ok':True}

@app.post('/api/admin/login')
async def login(a:AdminAuth):
    if not admin_ok(a.password): raise HTTPException(401,'Falsches Passwort')
    return {'ok':True}
@app.post('/api/admin/reorder')
async def reorder(x:Reorder,x_admin_password:str=Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401,'Nicht autorisiert')
    with conn() as c:
        for pos,i in enumerate(x.ids,1): c.execute("UPDATE queue SET position=? WHERE id=? AND status='queued'",(pos,i))
    await broadcast(); return {'ok':True}
@app.post('/api/admin/skip')
async def skip(x_admin_password:str=Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401,'Nicht autorisiert')
    with conn() as c: c.execute("UPDATE queue SET status='skipped',finished_at=CURRENT_TIMESTAMP WHERE status='playing'")
    await broadcast(); await start_next(); return {'ok':True}
@app.delete('/api/admin/queue/{item_id}')
async def delete(item_id:int,x_admin_password:str=Header(default='')):
    if not admin_ok(x_admin_password): raise HTTPException(401,'Nicht autorisiert')
    with conn() as c: c.execute("DELETE FROM queue WHERE id=? AND status='queued'",(item_id,))
    await broadcast(); return {'ok':True}
@app.post('/api/admin/lock')
async def lock(a:AdminAuth):
    if not admin_ok(a.password): raise HTTPException(401,'Nicht autorisiert')
    new='false' if setting('queue_locked','false')=='true' else 'true'; set_setting('queue_locked',new)
    await broadcast(); return {'locked':new=='true'}
@app.websocket('/ws')
async def ws(websocket:WebSocket):
    await websocket.accept(); clients.add(websocket); await websocket.send_json(await snapshot())
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: clients.discard(websocket)
