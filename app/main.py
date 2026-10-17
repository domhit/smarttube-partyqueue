import asyncio, random, secrets, time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import httpx
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .config import settings
from .db import conn, init_db, setting, set_setting
from .youtube import parse_video_id, playlist_items, quota_status, search_youtube, video_details

DEVICES = settings.parsed_devices(); DEVICE_IDS = {x['id'] for x in DEVICES}
clients = set(); locks = {}
playback = {}
idle_tasks = {}
prestart_guard_until = {}
class AddItem(BaseModel): video_id: Optional[str]=None; url: Optional[str]=None; requested_by: str='Gast'; target_tv: Optional[str]=None
class AdminAuth(BaseModel): password: str
class TvBody(BaseModel): target_tv: str
class Reorder(BaseModel): ids: list[int]; target_tv: str
class BaseAdd(BaseModel): video_id: Optional[str]=None; url: Optional[str]=None; history_id: Optional[int]=None
class PlaylistImport(BaseModel): playlist: str
class ProgressBody(BaseModel):
    target_tv: str
    state: str
    media_position: float = 0
    app_id: Optional[str] = None

def admin_ok(v): return secrets.compare_digest(v or '', settings.admin_password)
def require_admin(v):
    if not admin_ok(v): raise HTTPException(401,'Nicht autorisiert')
def valid_tv(v):
    tv=v or settings.default_tv
    if tv not in DEVICE_IDS: raise HTTPException(400,f'Unbekanntes TV-Gerät: {tv}')
    return tv

def base_rows():
    with conn() as c: return [dict(r) for r in c.execute('SELECT * FROM base_playlist ORDER BY position,id')]

async def snapshot():
    with conn() as c:
        q=[dict(r) for r in c.execute("SELECT * FROM queue WHERE status='queued' ORDER BY target_tv,position,id")]
        cur=[dict(r) for r in c.execute("SELECT * FROM queue WHERE status='playing' ORDER BY started_at DESC")]
        hist=[dict(r) for r in c.execute("SELECT * FROM queue WHERE status IN ('played','skipped') ORDER BY finished_at DESC LIMIT 100")]
    current_map={x['target_tv']:x for x in cur}
    pb={}
    now=time.monotonic()
    for tv,data in playback.items():
        position=float(data.get('media_position',0))
        if data.get('state')=='playing': position += max(0,now-data.get('received_monotonic',now))
        duration=float(current_map.get(tv,{}).get('duration_seconds') or 0)
        pb[tv]={'state':data.get('state','idle'),'media_position':min(position,duration) if duration else position,'duration':duration,'app_id':data.get('app_id'),'updated_at':data.get('updated_at')}
    return {'devices':DEVICES,'default_tv':settings.default_tv,'queue':q,'current':current_map,'playback':pb,'history':hist,'base_playlist':base_rows(),'quota':quota_status(),'locked':setting('queue_locked','false')=='true','base_enabled':setting('base_playlist_enabled','true')=='true'}

async def broadcast():
    data=await snapshot(); dead=[]
    for ws in clients:
        try: await ws.send_json(data)
        except Exception: dead.append(ws)
    for ws in dead: clients.discard(ws)

async def ha_play(item):
    endpoint=f"{settings.ha_url.rstrip('/')}/api/webhook/{settings.ha_webhook_id}"
    payload={'url':f"https://www.youtube.com/watch?v={item['video_id']}",'video_id':item['video_id'],'queue_item_id':item['id'],'target_tv':item['target_tv'],'smarttube_package':settings.smarttube_package}
    async with httpx.AsyncClient(timeout=15) as client:
        response=await client.post(endpoint,json=payload); response.raise_for_status()

def choose_base(c,target_tv):
    enabled=[dict(r) for r in c.execute('SELECT * FROM base_playlist WHERE enabled=1')]
    if not enabled:return None
    recent=[r['base_item_id'] for r in c.execute('SELECT base_item_id FROM base_play_history WHERE target_tv=? ORDER BY played_at DESC,id DESC LIMIT ?',(target_tv,settings.base_playlist_recent_exclude))]
    candidates=[x for x in enabled if x['id'] not in recent] or enabled
    item=random.choice(candidates)
    c.execute('INSERT INTO base_play_history(target_tv,base_item_id) VALUES(?,?)',(target_tv,item['id']))
    return item

async def start_next(target_tv, allow_base=True):
    target_tv=valid_tv(target_tv); lock=locks.setdefault(target_tv,asyncio.Lock())
    async with lock:
        if setting('playback_enabled','true')!='true':return False
        with conn() as c:
            if c.execute("SELECT 1 FROM queue WHERE status='playing' AND target_tv=?",(target_tv,)).fetchone():return False
            row=c.execute("SELECT * FROM queue WHERE status='queued' AND target_tv=? ORDER BY position,id LIMIT 1",(target_tv,)).fetchone()
            if row:
                item=dict(row); c.execute("UPDATE queue SET status='playing',started_at=CURRENT_TIMESTAMP WHERE id=?",(item['id'],))
            elif allow_base and setting('base_playlist_enabled','true')=='true':
                base=choose_base(c,target_tv)
                if not base:return False
                cur=c.execute("INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,target_tv,position,source,status,started_at) VALUES(?,?,?,?,?,'Grundplaylist',?,0,'base','playing',CURRENT_TIMESTAMP)",(base['video_id'],base['title'],base['channel'],base['thumbnail'],base['duration_seconds'],target_tv))
                item=dict(base); item.update({'id':cur.lastrowid,'target_tv':target_tv,'source':'base'})
            else:return False
        try: await ha_play(item)
        except Exception:
            with conn() as c:c.execute("UPDATE queue SET status='queued',started_at=NULL WHERE id=?",(item['id'],))
            raise
        await broadcast(); return True

async def get_detail(video_id=None,url=None):
    vid=video_id or parse_video_id(url or '')
    if not vid: raise HTTPException(400,'Ungültige YouTube-URL oder Video-ID')
    rows=await video_details([vid])
    if not rows:raise HTTPException(404,'Video nicht gefunden')
    d=rows[0]
    if d['is_live'] or not d['embeddable']:raise HTTPException(400,'Video nicht zulässig')
    if d['duration_seconds']>settings.max_video_minutes*60:raise HTTPException(400,f'Video länger als {settings.max_video_minutes} Minuten')
    return d

@asynccontextmanager
async def lifespan(app): init_db(); yield
app=FastAPI(title='SmartTube PartyQueue',version='2.3.0',lifespan=lifespan)
BASE=Path(__file__).parent; app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
@app.get('/')
async def guest():return FileResponse(BASE/'static/guest.html')
@app.get('/host')
async def host():return FileResponse(BASE/'static/host.html')
@app.get('/api/health')
async def health():return {'ok':True,'version':'2.3.0','devices':DEVICES}
@app.get('/api/state')
async def state():return await snapshot()
@app.get('/api/search')
async def search(q:str):
    try:return await search_youtube(q)
    except (ValueError,RuntimeError) as e:raise HTTPException(400,str(e))
    except httpx.HTTPStatusError as e:raise HTTPException(502,e.response.text[:500])

@app.post('/api/queue')
async def add(item:AddItem):
    if setting('queue_locked','false')=='true':raise HTTPException(423,'Queue ist gesperrt')
    tv=valid_tv(item.target_tv); d=await get_detail(item.video_id,item.url); guest=(item.requested_by.strip() or 'Gast')[:40]
    with conn() as c:
        if c.execute("SELECT 1 FROM queue WHERE video_id=? AND target_tv=? AND status IN ('queued','playing')",(d['video_id'],tv)).fetchone():raise HTTPException(409,'Titel bereits eingeplant')
        count=c.execute("SELECT COUNT(*) n FROM queue WHERE requested_by=? AND target_tv=? AND status='queued'",(guest,tv)).fetchone()['n']
        if count>=settings.max_requests_per_guest:raise HTTPException(429,f'Maximal {settings.max_requests_per_guest} offene Wünsche pro Gast und TV')
        pos=c.execute("SELECT COALESCE(MAX(position),0)+1 n FROM queue WHERE target_tv=? AND status='queued'",(tv,)).fetchone()['n']
        cur=c.execute('INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,target_tv,position) VALUES(?,?,?,?,?,?,?,?)',(d['video_id'],d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],guest,tv,pos))
    await broadcast(); await start_next(tv); return {'ok':True,'id':cur.lastrowid}

async def finish_and_advance(tv, reason):
    tv=valid_tv(tv)
    with conn() as c:
        changed=c.execute("UPDATE queue SET status='played',finished_at=CURRENT_TIMESTAMP WHERE status='playing' AND target_tv=?",(tv,)).rowcount
    if not changed: return False
    await broadcast()
    await start_next(tv)
    return True

async def idle_fallback(tv):
    await asyncio.sleep(settings.idle_fallback_delay)
    data=playback.get(tv,{})
    if data.get('state')!='idle': return
    if time.monotonic()<prestart_guard_until.get(tv,0): return
    await finish_and_advance(tv,'idle')

@app.post('/api/playback/progress')
async def playback_progress(body:ProgressBody,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password); tv=valid_tv(body.target_tv)
    playback[tv]={'state':body.state,'media_position':max(0,float(body.media_position or 0)),'app_id':body.app_id,'received_monotonic':time.monotonic(),'updated_at':time.time()}
    with conn() as c: current=c.execute("SELECT * FROM queue WHERE status='playing' AND target_tv=? ORDER BY started_at DESC LIMIT 1",(tv,)).fetchone()
    triggered=False
    if current and body.state=='playing' and body.app_id==settings.smarttube_package:
        duration=float(current['duration_seconds'] or 0)
        if duration>0 and body.media_position>=max(0,duration-settings.prestart_seconds):
            prestart_guard_until[tv]=time.monotonic()+settings.prestart_idle_guard
            triggered=await finish_and_advance(tv,'prestart')
    if body.state=='idle' and time.monotonic()>=prestart_guard_until.get(tv,0):
        old=idle_tasks.get(tv)
        if old and not old.done(): old.cancel()
        idle_tasks[tv]=asyncio.create_task(idle_fallback(tv))
    await broadcast()
    return {'ok':True,'prestart_triggered':triggered}

@app.post('/api/playback/end')
async def playback_end(body:TvBody,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password)
    return {'ok':True,'advanced':await finish_and_advance(body.target_tv,'manual')}

@app.post('/api/admin/login')
async def login(body:AdminAuth):require_admin(body.password); return {'ok':True}
@app.post('/api/admin/start')
async def start(body:TvBody,x_admin_password:str=Header(default='')):require_admin(x_admin_password); return {'started':await start_next(body.target_tv)}
@app.post('/api/admin/skip')
async def skip(body:TvBody,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password); tv=valid_tv(body.target_tv)
    with conn() as c:c.execute("UPDATE queue SET status='skipped',finished_at=CURRENT_TIMESTAMP WHERE status='playing' AND target_tv=?",(tv,))
    await broadcast(); await start_next(tv); return {'ok':True}
@app.post('/api/admin/reorder')
async def reorder(body:Reorder,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password); tv=valid_tv(body.target_tv)
    with conn() as c:
        for pos,item_id in enumerate(body.ids,1):c.execute("UPDATE queue SET position=? WHERE id=? AND target_tv=? AND status='queued'",(pos,item_id,tv))
    await broadcast(); return {'ok':True}
@app.delete('/api/admin/queue/{item_id}')
async def delete_queue(item_id:int,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password)
    with conn() as c:c.execute("DELETE FROM queue WHERE id=? AND status='queued'",(item_id,))
    await broadcast(); return {'ok':True}
@app.post('/api/admin/lock')
async def lock(body:AdminAuth):
    require_admin(body.password); new='false' if setting('queue_locked','false')=='true' else 'true'; set_setting('queue_locked',new); await broadcast(); return {'locked':new=='true'}
@app.post('/api/admin/base/toggle')
async def base_toggle(body:AdminAuth):
    require_admin(body.password); new='false' if setting('base_playlist_enabled','true')=='true' else 'true'; set_setting('base_playlist_enabled',new); await broadcast(); return {'enabled':new=='true'}

@app.post('/api/admin/base')
async def base_add(body:BaseAdd,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password)
    if body.history_id:
        with conn() as c:row=c.execute('SELECT * FROM queue WHERE id=?',(body.history_id,)).fetchone()
        if not row:raise HTTPException(404,'Verlaufseintrag nicht gefunden')
        d=dict(row); added_from='history'
    else:d=await get_detail(body.video_id,body.url); added_from='manual'
    with conn() as c:
        pos=c.execute('SELECT COALESCE(MAX(position),0)+1 n FROM base_playlist').fetchone()['n']
        c.execute('INSERT OR IGNORE INTO base_playlist(video_id,title,channel,thumbnail,duration_seconds,position,added_from) VALUES(?,?,?,?,?,?,?)',(d['video_id'],d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],pos,added_from))
    await broadcast(); return {'ok':True}
@app.post('/api/admin/base/import')
async def base_import(body:PlaylistImport,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password)
    try:items=await playlist_items(body.playlist)
    except ValueError as e:raise HTTPException(400,str(e))
    added=0
    with conn() as c:
        pos=c.execute('SELECT COALESCE(MAX(position),0) n FROM base_playlist').fetchone()['n']
        for d in items:
            if d['is_live'] or not d['embeddable'] or d['duration_seconds']>settings.max_video_minutes*60:continue
            pos+=1; cur=c.execute('INSERT OR IGNORE INTO base_playlist(video_id,title,channel,thumbnail,duration_seconds,position,added_from) VALUES(?,?,?,?,?,?,?)',(d['video_id'],d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],pos,'youtube_playlist')); added+=cur.rowcount
    await broadcast(); return {'ok':True,'added':added,'found':len(items)}
@app.patch('/api/admin/base/{item_id}/toggle')
async def base_item_toggle(item_id:int,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password)
    with conn() as c:c.execute('UPDATE base_playlist SET enabled=CASE enabled WHEN 1 THEN 0 ELSE 1 END WHERE id=?',(item_id,))
    await broadcast(); return {'ok':True}
@app.delete('/api/admin/base/{item_id}')
async def base_delete(item_id:int,x_admin_password:str=Header(default='')):
    require_admin(x_admin_password)
    with conn() as c:c.execute('DELETE FROM base_playlist WHERE id=?',(item_id,))
    await broadcast(); return {'ok':True}

@app.websocket('/ws')
async def ws(websocket:WebSocket):
    await websocket.accept(); clients.add(websocket); await websocket.send_json(await snapshot())
    try:
        while True:await websocket.receive_text()
    except WebSocketDisconnect:clients.discard(websocket)
