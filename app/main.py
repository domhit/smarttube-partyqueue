import asyncio,csv,io,json,random,secrets,time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import httpx
from fastapi import FastAPI,Header,HTTPException,WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse,HTMLResponse,PlainTextResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .config import settings
from .db import conn,init_db
from .youtube import video_id,details,search,playlist,quota
D=settings.parsed_devices();IDS={x['id'] for x in D};clients=set();locks={};pb={};guard={};idle={}
class Add(BaseModel):video_id:Optional[str]=None;url:Optional[str]=None;requested_by:str='Gast';guest_id:str='';target_tv:Optional[str]=None
class Auth(BaseModel):password:str
class Tv(BaseModel):target_tv:str
class QueueReorder(BaseModel):target_tv:str;ids:list[int]
class Progress(BaseModel):target_tv:str;state:str;media_position:float=0;app_id:Optional[str]=None
class Vote(BaseModel):guest_id:str
class PartyPatch(BaseModel):name:Optional[str]=None;playlist_id:Optional[int]=None;allowed_devices:Optional[list[str]]=None;default_tv:Optional[str]=None;request_limit:Optional[int]=None;repeat_window:Optional[int]=None;queue_locked:Optional[bool]=None;upvote_sort:Optional[bool]=None;detect_external_skip:Optional[bool]=None;playlist_enabled:Optional[bool]=None
class PlaylistCreate(BaseModel):name:str
class PlaylistRename(BaseModel):name:str
class PlaylistClone(BaseModel):name:str
class PlaylistAdd(BaseModel):playlist_id:int;video_id:Optional[str]=None;url:Optional[str]=None;history_id:Optional[int]=None
class PlaylistImport(BaseModel):playlist_id:int;playlist:str
def au(x):
 if not secrets.compare_digest(x or'',settings.admin_password):raise HTTPException(401,'Nicht autorisiert')
def party():
 with conn() as c:r=c.execute('SELECT * FROM parties WHERE active=1 ORDER BY id DESC LIMIT 1').fetchone();return dict(r) if r else None
def allow(p):return [x for x in p['allowed_devices'].split(',') if x]
def tvok(x,p):
 x=x or p['default_tv']
 if x not in allow(p):raise HTTPException(403,'Abspieler nicht freigegeben')
 return x
def pub(p):return {**p,'allowed_devices':[x for x in D if x['id'] in allow(p)]}
async def state():
 p=party()
 with conn() as c:
  pls=[dict(r) for r in c.execute('SELECT p.*,COUNT(i.id) item_count FROM playlists p LEFT JOIN playlist_items i ON i.playlist_id=p.id GROUP BY p.id ORDER BY p.name')]
  if not p:return {'party':None,'playlists':pls,'queue':[],'current':{},'history':[],'playback':{},'quota':quota()}
  q=[dict(r) for r in c.execute("SELECT * FROM queue WHERE party_id=? AND status='queued' ORDER BY admin_priority DESC,CASE WHEN ?=1 THEN votes END DESC,position,id",(p['id'],p['upvote_sort']))];cu=[dict(r) for r in c.execute("SELECT * FROM queue WHERE party_id=? AND status='playing'",(p['id'],))];hi=[dict(r) for r in c.execute("SELECT * FROM queue WHERE party_id=? AND status IN ('played','skipped') ORDER BY finished_at DESC LIMIT 100",(p['id'],))]
 cm={x['target_tv']:x for x in cu};now=time.monotonic();play={}
 for tv,x in pb.items():
  pos=x['media_position']+(max(0,now-x['received']) if x['state']=='playing' else 0);du=float(cm.get(tv,{}).get('duration_seconds')or 0);play[tv]={**x,'media_position':min(pos,du) if du else pos}
 return {'party':pub(p),'devices':pub(p)['allowed_devices'],'all_devices':D,'playlists':pls,'queue':q,'current':cm,'history':hi,'playback':play,'quota':quota()}
async def cast():
 s=await state();dead=[]
 for w in clients:
  try:await w.send_json(s)
  except:dead.append(w)
 for w in dead:clients.discard(w)
async def play(x):
 async with httpx.AsyncClient(timeout=15) as c:r=await c.post(f"{settings.ha_url.rstrip('/')}/api/webhook/{settings.ha_webhook_id}",json={'url':f"https://www.youtube.com/watch?v={x['video_id']}",'target_tv':x['target_tv'],'smarttube_package':settings.smarttube_package});r.raise_for_status()
def base(c,p,tv):
 if not p['playlist_enabled'] or not p['playlist_id']:return None
 a=[dict(r) for r in c.execute('SELECT * FROM playlist_items WHERE playlist_id=? AND enabled=1',(p['playlist_id'],))]
 if not a:return None
 used=[r['playlist_item_id'] for r in c.execute('SELECT playlist_item_id FROM base_play_history WHERE party_id=? AND target_tv=? ORDER BY id DESC LIMIT ?',(p['id'],tv,settings.base_playlist_recent_exclude))];x=random.choice([z for z in a if z['id'] not in used]or a);c.execute('INSERT INTO base_play_history(target_tv,playlist_item_id,party_id) VALUES(?,?,?)',(tv,x['id'],p['id']));return x
async def nxt(tv):
 p=party();tv=tvok(tv,p);l=locks.setdefault(tv,asyncio.Lock())
 async with l:
  with conn() as c:
   if c.execute("SELECT 1 FROM queue WHERE party_id=? AND target_tv=? AND status='playing'",(p['id'],tv)).fetchone():return False
   r=c.execute("SELECT * FROM queue WHERE party_id=? AND target_tv=? AND status='queued' ORDER BY admin_priority DESC,CASE WHEN ?=1 THEN votes END DESC,position,id LIMIT 1",(p['id'],tv,p['upvote_sort'])).fetchone()
   if r:x=dict(r);c.execute("UPDATE queue SET status='playing',started_at=CURRENT_TIMESTAMP WHERE id=?",(x['id'],))
   else:
    b=base(c,p,tv)
    if not b:return False
    k=c.execute("INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,target_tv,position,source,status,party_id,playlist_id,started_at) VALUES(?,?,?,?,?,'Grundplaylist',?,0,'base','playing',?,?,CURRENT_TIMESTAMP)",(b['video_id'],b['title'],b['channel'],b['thumbnail'],b['duration_seconds'],tv,p['id'],p['playlist_id']));x={**b,'id':k.lastrowid,'target_tv':tv}
  await play(x);await cast();return True
async def done(tv,st='played'):
 p=party();tv=tvok(tv,p)
 with conn() as c:n=c.execute("UPDATE queue SET status=?,finished_at=CURRENT_TIMESTAMP WHERE party_id=? AND target_tv=? AND status='playing'",(st,p['id'],tv)).rowcount
 if n:await cast();await nxt(tv)
async def metadata(v=None,u=None):
 v=v or video_id(u or'');a=await details([v]) if v else[]
 if not a:raise HTTPException(400,'Video nicht verfügbar')
 return a[0]
@asynccontextmanager
async def life(app):init_db();yield
app=FastAPI(version='2.5.2',lifespan=life);B=Path(__file__).parent;app.mount('/static',StaticFiles(directory=B/'static'),name='static')
@app.get('/')
async def g():return FileResponse(B/'static/guest.html')
@app.get('/host')
async def h():return FileResponse(B/'static/host.html')
@app.get('/api/health')
async def health():return {'ok':True,'version':'2.5.2'}
@app.get('/api/state')
async def st():return await state()
@app.get('/api/party/public')
async def pp():return pub(party())
@app.get('/api/search')
async def sr(q:str):return await search(q)
@app.post('/api/queue')
async def add(b:Add):
 p=party()
 if p['queue_locked']:raise HTTPException(423,'Musikwünsche sind gesperrt')
 tv=tvok(b.target_tv,p);d=await metadata(b.video_id,b.url)
 with conn() as c:
  if c.execute("SELECT 1 FROM queue WHERE party_id=? AND target_tv=? AND video_id=? AND status IN ('queued','playing')",(p['id'],tv,d['video_id'])).fetchone():raise HTTPException(409,'Titel bereits eingeplant')
  if p['repeat_window'] and c.execute("SELECT 1 FROM (SELECT video_id FROM queue WHERE party_id=? AND target_tv=? AND status IN ('played','skipped') ORDER BY finished_at DESC LIMIT ?) WHERE video_id=?",(p['id'],tv,p['repeat_window'],d['video_id'])).fetchone():raise HTTPException(409,'Titel lief vor Kurzem bereits')
  if p['request_limit'] and c.execute("SELECT COUNT(*) n FROM queue WHERE party_id=? AND guest_id=? AND status='queued'",(p['id'],b.guest_id)).fetchone()['n']>=p['request_limit']:raise HTTPException(429,f'Maximal {p["request_limit"]} offene Wünsche')
  pos=c.execute("SELECT COALESCE(MAX(position),0)+1 n FROM queue WHERE party_id=? AND target_tv=? AND status='queued'",(p['id'],tv)).fetchone()['n'];r=c.execute('INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,guest_id,target_tv,position,party_id) VALUES(?,?,?,?,?,?,?,?,?,?)',(d['video_id'],d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],b.requested_by,b.guest_id,tv,pos,p['id']))
 await cast();await nxt(tv);return {'id':r.lastrowid,'position':pos}
@app.post('/api/queue/{qid}/vote')
async def vote(qid:int,b:Vote):
 with conn() as c:
  old=c.execute('SELECT 1 FROM votes WHERE queue_id=? AND guest_id=?',(qid,b.guest_id)).fetchone();c.execute('DELETE FROM votes WHERE queue_id=? AND guest_id=?',(qid,b.guest_id)) if old else c.execute('INSERT INTO votes VALUES(?,?,CURRENT_TIMESTAMP)',(qid,b.guest_id));c.execute('UPDATE queue SET votes=votes+? WHERE id=?',(-1 if old else 1,qid))
 await cast();return {'voted':not bool(old)}
@app.post('/api/admin/login')
async def login(b:Auth):au(b.password);return {'ok':True}
@app.post('/api/admin/start')
async def start(b:Tv,x_admin_password:str=Header(default='')):au(x_admin_password);return {'started':await nxt(b.target_tv)}
@app.post('/api/admin/skip')
async def skip(b:Tv,x_admin_password:str=Header(default='')):au(x_admin_password);await done(b.target_tv,'skipped');return {'ok':True}
@app.post('/api/admin/queue/reorder')
async def queue_reorder(b:QueueReorder,x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party();tv=tvok(b.target_tv,p)
 with conn() as c:
  valid={r['id'] for r in c.execute("SELECT id FROM queue WHERE party_id=? AND target_tv=? AND status='queued'",(p['id'],tv))}
  if set(b.ids)!=valid:raise HTTPException(409,'Queue hat sich geändert. Bitte Ansicht neu laden.')
  total=len(b.ids)
  for index,qid in enumerate(b.ids):c.execute("UPDATE queue SET admin_priority=? WHERE id=?",(total-index,qid))
 await cast();return {'ok':True}
@app.post('/api/admin/queue/{qid}/next')
async def queue_next(qid:int,x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party()
 with conn() as c:
  row=c.execute("SELECT target_tv FROM queue WHERE id=? AND party_id=? AND status='queued'",(qid,p['id'])).fetchone()
  if not row:raise HTTPException(404,'Queue-Eintrag nicht gefunden')
  top=c.execute("SELECT COALESCE(MAX(admin_priority),0)+1 n FROM queue WHERE party_id=? AND target_tv=? AND status='queued'",(p['id'],row['target_tv'])).fetchone()['n']
  c.execute('UPDATE queue SET admin_priority=? WHERE id=?',(top,qid))
 await cast();return {'ok':True}
@app.delete('/api/admin/queue/{qid}')
async def queue_delete(qid:int,x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party()
 with conn() as c:
  n=c.execute("DELETE FROM queue WHERE id=? AND party_id=? AND status='queued'",(qid,p['id'])).rowcount
 if not n:raise HTTPException(404,'Queue-Eintrag nicht gefunden oder bereits gestartet')
 await cast();return {'ok':True}
@app.patch('/api/admin/party')
async def patch(b:PartyPatch,x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party();d=b.model_dump(exclude_none=True)
 if 'allowed_devices'in d:d['allowed_devices']=','.join(d['allowed_devices'])
 with conn() as c:
  for k,v in d.items():c.execute(f'UPDATE parties SET {k}=? WHERE id=?',(int(v) if isinstance(v,bool) else v,p['id']))
 await cast();return {'ok':True}
@app.post('/api/playback/progress')
async def progress(b:Progress,x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party();tv=tvok(b.target_tv,p);old=pb.get(tv,{});pb[tv]={'state':b.state,'media_position':max(0,b.media_position),'app_id':b.app_id,'received':time.monotonic()}
 with conn() as c:r=c.execute("SELECT * FROM queue WHERE party_id=? AND target_tv=? AND status='playing'",(p['id'],tv)).fetchone()
 if r and b.state=='playing' and b.app_id==settings.smarttube_package:
  if r['duration_seconds'] and b.media_position>=r['duration_seconds']-settings.prestart_seconds:guard[tv]=time.monotonic()+settings.prestart_idle_guard;await done(tv)
  elif p['detect_external_skip'] and old.get('media_position',0)>=settings.external_skip_min_previous and b.media_position<=settings.external_skip_max_new and time.monotonic()>=guard.get(tv,0):await done(tv,'skipped')
 if b.state=='idle' and time.monotonic()>=guard.get(tv,0):
  async def f():
   await asyncio.sleep(settings.idle_fallback_delay)
   if pb.get(tv,{}).get('state')=='idle' and time.monotonic()>=guard.get(tv,0):await done(tv)
  if tv in idle and not idle[tv].done():idle[tv].cancel()
  idle[tv]=asyncio.create_task(f())
 await cast();return {'ok':True}
def pname(c,name,exclude=None):
 q='SELECT 1 FROM playlists WHERE lower(name)=lower(?)'+(' AND id<>?' if exclude else'');return c.execute(q,(name,exclude) if exclude else(name,)).fetchone()
@app.post('/api/admin/playlists')
async def plnew(b:PlaylistCreate,x_admin_password:str=Header(default='')):
 au(x_admin_password);n=b.name.strip()
 with conn() as c:
  if not n:raise HTTPException(400,'Playlistname fehlt')
  if pname(c,n):raise HTTPException(409,'Playlistname existiert bereits')
  r=c.execute('INSERT INTO playlists(name) VALUES(?)',(n,))
 await cast();return {'id':r.lastrowid}
@app.get('/api/admin/playlists/{pid}/items')
async def plitems(pid:int,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:return [dict(r) for r in c.execute('SELECT * FROM playlist_items WHERE playlist_id=? ORDER BY position,id',(pid,))]
@app.patch('/api/admin/playlists/{pid}')
async def plrename(pid:int,b:PlaylistRename,x_admin_password:str=Header(default='')):
 au(x_admin_password);n=b.name.strip()
 with conn() as c:
  if pname(c,n,pid):raise HTTPException(409,'Playlistname existiert bereits')
  c.execute('UPDATE playlists SET name=? WHERE id=?',(n,pid))
 await cast();return {'ok':True}
@app.post('/api/admin/playlists/{pid}/clone')
async def plclone(pid:int,b:PlaylistClone,x_admin_password:str=Header(default='')):
 au(x_admin_password);n=b.name.strip()
 with conn() as c:
  if pname(c,n):raise HTTPException(409,'Playlistname existiert bereits')
  r=c.execute('INSERT INTO playlists(name) VALUES(?)',(n,));nid=r.lastrowid;c.execute("INSERT INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from) SELECT ?,video_id,title,channel,thumbnail,duration_seconds,enabled,position,'clone' FROM playlist_items WHERE playlist_id=?",(nid,pid))
 await cast();return {'id':nid}
@app.delete('/api/admin/playlists/{pid}')
async def pldel(pid:int,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:
  if c.execute('SELECT 1 FROM parties WHERE playlist_id=?',(pid,)).fetchone():raise HTTPException(409,'Playlist ist noch einer Party zugeordnet')
  c.execute('DELETE FROM playlists WHERE id=?',(pid,))
 await cast();return {'ok':True}
@app.post('/api/admin/playlists/item')
async def pladd(b:PlaylistAdd,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 if b.history_id:
  with conn() as c:r=c.execute('SELECT * FROM queue WHERE id=?',(b.history_id,)).fetchone()
  d=dict(r);src='history'
 else:d=await metadata(b.video_id,b.url);src='manual'
 with conn() as c:pos=c.execute('SELECT COALESCE(MAX(position),0)+1 n FROM playlist_items WHERE playlist_id=?',(b.playlist_id,)).fetchone()['n'];c.execute('INSERT OR IGNORE INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,position,added_from) VALUES(?,?,?,?,?,?,?,?)',(b.playlist_id,d['video_id'],d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],pos,src))
 await cast();return {'ok':True}
@app.post('/api/admin/playlists/import')
async def plimport(b:PlaylistImport,x_admin_password:str=Header(default='')):
 au(x_admin_password);a=await playlist(b.playlist);n=0
 with conn() as c:
  pos=c.execute('SELECT COALESCE(MAX(position),0) n FROM playlist_items WHERE playlist_id=?',(b.playlist_id,)).fetchone()['n']
  for d in a:
   pos+=1;n+=c.execute("INSERT OR IGNORE INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,position,added_from) VALUES(?,?,?,?,?,?,?,'youtube_playlist')",(b.playlist_id,d['video_id'],d['title'],d['channel'],d['thumbnail'],d['duration_seconds'],pos)).rowcount
 await cast();return {'found':len(a),'added':n}
@app.delete('/api/admin/playlists/item/{iid}')
async def pldelitem(iid:int,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:c.execute('DELETE FROM playlist_items WHERE id=?',(iid,))
 await cast();return {'ok':True}
@app.websocket('/ws')
async def ws(w:WebSocket):
 await w.accept();clients.add(w);await w.send_json(await state())
 try:
  while True:await w.receive_text()
 except WebSocketDisconnect:clients.discard(w)

@app.get('/api/admin/stats')
async def stats(x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:return [dict(r) for r in c.execute("SELECT video_id,title,COUNT(*) played_total,SUM(CASE WHEN source='request' THEN 1 ELSE 0 END) requested_total,SUM(CASE WHEN status='skipped' THEN 1 ELSE 0 END) skipped_total,SUM(votes) votes_total FROM queue WHERE status IN ('played','skipped') GROUP BY video_id,title ORDER BY played_total DESC LIMIT 100")]
@app.get('/api/party/{pid}/export/{fmt}')
async def export(pid:int,fmt:str,password:str='',x_admin_password:str=Header(default='')):
 au(x_admin_password or password)
 with conn() as c:rows=[dict(r) for r in c.execute("SELECT finished_at,title,channel,video_id,source,requested_by,votes,target_tv,status FROM queue WHERE party_id=? AND status IN ('played','skipped') ORDER BY finished_at",(pid,))];p=c.execute('SELECT name FROM parties WHERE id=?',(pid,)).fetchone()
 if fmt=='json':return StreamingResponse(io.BytesIO(json.dumps(rows,ensure_ascii=False,indent=2).encode()),media_type='application/json')
 if fmt=='csv':
  o=io.StringIO();w=csv.DictWriter(o,fieldnames=rows[0].keys() if rows else ['title']);w.writeheader();w.writerows(rows);return StreamingResponse(io.BytesIO(o.getvalue().encode('utf-8-sig')),media_type='text/csv')
 if fmt=='m3u':return PlainTextResponse('#EXTM3U\n'+''.join(f"#EXTINF:-1,{r['title']}\nhttps://www.youtube.com/watch?v={r['video_id']}\n" for r in rows))
 if fmt=='html':return HTMLResponse('<h1>'+p['name']+'</h1><ol>'+''.join(f"<li><a href=https://www.youtube.com/watch?v={r['video_id']}>{r['title']}</a></li>" for r in rows)+'</ol>')
 raise HTTPException(400,'Format unbekannt')
