import asyncio,csv,html,io,json,random,secrets,time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
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
class PlaylistReorder(BaseModel):playlist_id:int;ids:list[int]
class PlaylistBulk(BaseModel):source_playlist_id:int;target_playlist_id:int;item_ids:list[int];mode:str='copy'
class PlaylistItemPatch(BaseModel):enabled:bool
class PartyCreate(BaseModel):
 name:str
 clone_current:bool=False
 playlist_id:Optional[int]=None
 allowed_devices:Optional[list[str]]=None
 default_tv:Optional[str]=None
 request_limit:Optional[int]=None
 repeat_window:Optional[int]=None
 upvote_sort:Optional[bool]=None
 detect_external_skip:Optional[bool]=None
 playlist_enabled:Optional[bool]=None
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
  archive=[dict(r) for r in c.execute("SELECT p.id,p.name,p.active,p.started_at,p.ended_at,COUNT(CASE WHEN q.status IN ('played','skipped') THEN 1 END) played_total,SUM(CASE WHEN q.source='request' AND q.status IN ('played','skipped') THEN 1 ELSE 0 END) request_total,COALESCE(SUM(CASE WHEN q.status IN ('played','skipped') THEN q.votes ELSE 0 END),0) votes_total FROM parties p LEFT JOIN queue q ON q.party_id=p.id GROUP BY p.id ORDER BY p.started_at DESC,p.id DESC")]
  if not p:return {'party':None,'parties':archive,'playlists':pls,'queue':[],'current':{},'history':[],'playback':{},'quota':quota(),'devices':[],'all_devices':D}
  q=[dict(r) for r in c.execute("SELECT * FROM queue WHERE party_id=? AND status='queued' ORDER BY admin_priority DESC,CASE WHEN ?=1 THEN votes END DESC,position,id",(p['id'],p['upvote_sort']))];cu=[dict(r) for r in c.execute("SELECT * FROM queue WHERE party_id=? AND status='playing'",(p['id'],))];hi=[dict(r) for r in c.execute("SELECT * FROM queue WHERE party_id=? AND status IN ('played','skipped') ORDER BY finished_at DESC LIMIT 100",(p['id'],))]
 cm={x['target_tv']:x for x in cu};now=time.monotonic();play={}
 for tv,x in pb.items():
  pos=x['media_position']+(max(0,now-x['received']) if x['state']=='playing' else 0);du=float(cm.get(tv,{}).get('duration_seconds')or 0);play[tv]={**x,'media_position':min(pos,du) if du else pos}
 return {'party':pub(p),'parties':archive,'devices':pub(p)['allowed_devices'],'all_devices':D,'playlists':pls,'queue':q,'current':cm,'history':hi,'playback':play,'quota':quota()}
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
app=FastAPI(version='2.7.1',lifespan=life);B=Path(__file__).parent;app.mount('/static',StaticFiles(directory=B/'static'),name='static')
@app.get('/')
async def g():return FileResponse(B/'static/guest.html')
@app.get('/host')
async def h():return FileResponse(B/'static/host.html')
@app.get('/api/health')
async def health():return {'ok':True,'version':'2.7.1'}
@app.get('/api/state')
async def st():return await state()
@app.get('/api/party/public')
async def pp():
 p=party()
 if not p:raise HTTPException(404,'Derzeit läuft keine Party')
 return pub(p)
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

def close_active_party(c,p):
 if not p:return
 c.execute("UPDATE queue SET status='played',finished_at=COALESCE(finished_at,CURRENT_TIMESTAMP) WHERE party_id=? AND status='playing'",(p['id'],))
 c.execute("UPDATE queue SET status='cancelled',finished_at=COALESCE(finished_at,CURRENT_TIMESTAMP) WHERE party_id=? AND status='queued'",(p['id'],))
 c.execute("UPDATE parties SET active=0,queue_locked=1,ended_at=COALESCE(ended_at,CURRENT_TIMESTAMP) WHERE id=?",(p['id'],))

@app.post('/api/admin/party/close')
async def party_close(x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party()
 if not p:raise HTTPException(409,'Es läuft keine Party')
 with conn() as c:close_active_party(c,p)
 pb.clear();guard.clear();idle.clear();await cast();return {'ok':True,'party_id':p['id']}

@app.post('/api/admin/parties')
async def party_create(b:PartyCreate,x_admin_password:str=Header(default='')):
 au(x_admin_password);name=b.name.strip()
 if not name:raise HTTPException(400,'Partyname fehlt')
 current=party()
 with conn() as c:
  if current:close_active_party(c,current)
  if b.clone_current and current:
   values={k:current[k] for k in ('playlist_id','allowed_devices','default_tv','request_limit','repeat_window','upvote_sort','detect_external_skip','playlist_enabled')}
  else:
   allowed=b.allowed_devices or [x['id'] for x in D]
   values={'playlist_id':b.playlist_id or 1,'allowed_devices':','.join(allowed),'default_tv':b.default_tv or settings.default_tv,'request_limit':settings.max_requests_per_guest if b.request_limit is None else b.request_limit,'repeat_window':settings.base_playlist_recent_exclude if b.repeat_window is None else b.repeat_window,'upvote_sort':1 if b.upvote_sort is None else int(b.upvote_sort),'detect_external_skip':0 if b.detect_external_skip is None else int(b.detect_external_skip),'playlist_enabled':1 if b.playlist_enabled is None else int(b.playlist_enabled)}
  r=c.execute("INSERT INTO parties(name,playlist_id,allowed_devices,default_tv,request_limit,repeat_window,queue_locked,upvote_sort,detect_external_skip,playlist_enabled,active,started_at,ended_at) VALUES(?,?,?,?,?,?,0,?,?,?,?,CURRENT_TIMESTAMP,NULL)",(name,values['playlist_id'],values['allowed_devices'],values['default_tv'],values['request_limit'],values['repeat_window'],values['upvote_sort'],values['detect_external_skip'],values['playlist_enabled'],1))
 pb.clear();guard.clear();idle.clear();await cast();return {'ok':True,'id':r.lastrowid}

@app.get('/api/admin/parties')
async def parties_archive(x_admin_password:str=Header(default='')):
 au(x_admin_password);s=await state();return s.get('parties',[])
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
@app.post('/api/admin/playlists/reorder')
async def playlist_reorder(b:PlaylistReorder,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:
  valid={r['id'] for r in c.execute('SELECT id FROM playlist_items WHERE playlist_id=?',(b.playlist_id,))}
  if set(b.ids)!=valid or len(b.ids)!=len(valid):raise HTTPException(409,'Playlist hat sich geändert. Bitte Ansicht neu laden.')
  for position,item_id in enumerate(b.ids,1):c.execute('UPDATE playlist_items SET position=? WHERE id=? AND playlist_id=?',(position,item_id,b.playlist_id))
 await cast();return {'ok':True}
@app.post('/api/admin/playlists/bulk')
async def playlist_bulk(b:PlaylistBulk,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 if b.mode not in ('copy','move'):raise HTTPException(400,'Modus muss copy oder move sein')
 if b.source_playlist_id==b.target_playlist_id:raise HTTPException(400,'Quell- und Zielplaylist müssen unterschiedlich sein')
 if not b.item_ids:raise HTTPException(400,'Keine Titel ausgewählt')
 copied=0; skipped=0
 with conn() as c:
  if not c.execute('SELECT 1 FROM playlists WHERE id=?',(b.target_playlist_id,)).fetchone():raise HTTPException(404,'Zielplaylist nicht gefunden')
  placeholders=','.join('?' for _ in b.item_ids)
  rows=[dict(r) for r in c.execute(f'SELECT * FROM playlist_items WHERE playlist_id=? AND id IN ({placeholders})',(b.source_playlist_id,*b.item_ids))]
  if len(rows)!=len(set(b.item_ids)):raise HTTPException(409,'Mindestens ein ausgewählter Titel wurde zwischenzeitlich geändert')
  position=c.execute('SELECT COALESCE(MAX(position),0) n FROM playlist_items WHERE playlist_id=?',(b.target_playlist_id,)).fetchone()['n']
  for row in sorted(rows,key=lambda x:(x['position'],x['id'])):
   position+=1
   inserted=c.execute("INSERT OR IGNORE INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from) VALUES(?,?,?,?,?,?,?,?,?)",(b.target_playlist_id,row['video_id'],row['title'],row['channel'],row['thumbnail'],row['duration_seconds'],row['enabled'],position,'copy' if b.mode=='copy' else 'move')).rowcount
   copied+=inserted;skipped+=0 if inserted else 1
  if b.mode=='move':c.execute(f'DELETE FROM playlist_items WHERE playlist_id=? AND id IN ({placeholders})',(b.source_playlist_id,*b.item_ids))
  # Normalize source and target positions.
  for playlist_id in {b.source_playlist_id,b.target_playlist_id}:
   ids=[r['id'] for r in c.execute('SELECT id FROM playlist_items WHERE playlist_id=? ORDER BY position,id',(playlist_id,))]
   for pos,item_id in enumerate(ids,1):c.execute('UPDATE playlist_items SET position=? WHERE id=?',(pos,item_id))
 await cast();return {'ok':True,'copied':copied,'skipped':skipped,'mode':b.mode}
@app.patch('/api/admin/playlists/item/{iid}')
async def playlist_item_patch(iid:int,b:PlaylistItemPatch,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:
  if not c.execute('UPDATE playlist_items SET enabled=? WHERE id=?',(int(b.enabled),iid)).rowcount:raise HTTPException(404,'Playlist-Titel nicht gefunden')
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
def parse_db_time(value):
 if not value:return None
 try:
  dt=datetime.fromisoformat(str(value).replace(' ','T'))
  if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
  return dt.astimezone(ZoneInfo(settings.tz))
 except:return None

def duration_text(seconds):
 seconds=max(0,int(seconds or 0));hours,rest=divmod(seconds,3600);minutes=rest//60
 return f'{hours} Stunden {minutes} Minuten' if hours else f'{minutes} Minuten'

def party_recap_html(p,rows):
 safe=lambda x:html.escape(str(x or''))
 start=next((parse_db_time(r.get('started_at') or r.get('created_at')) for r in rows if parse_db_time(r.get('started_at') or r.get('created_at'))),parse_db_time(p.get('started_at')))
 end=parse_db_time(p.get('ended_at')) or next((parse_db_time(r.get('finished_at')) for r in reversed(rows) if r.get('finished_at')),None) or datetime.now(ZoneInfo(settings.tz))
 duration=max(0,(end-start).total_seconds()) if start else 0
 played=[r for r in rows if r['status']=='played'];skipped=[r for r in rows if r['status']=='skipped'];requests=[r for r in rows if r['source']=='request'];bases=[r for r in rows if r['source']=='base']
 requester_counts={};artist_counts={}
 for r in requests:
  name=(r.get('requested_by') or 'Gast').strip() or 'Gast';requester_counts[name]=requester_counts.get(name,0)+1
 for r in rows:
  artist=(r.get('channel') or 'Unbekannt').strip() or 'Unbekannt';artist_counts[artist]=artist_counts.get(artist,0)+1
 top_requester=max(requester_counts.items(),key=lambda x:(x[1],x[0])) if requester_counts else ('–',0)
 top_artist=max(artist_counts.items(),key=lambda x:(x[1],x[0])) if artist_counts else ('–',0)
 top_voted=max(rows,key=lambda r:(r.get('votes') or 0,r.get('title') or''),default=None)
 total_votes=sum(int(r.get('votes') or 0) for r in rows)
 date_base=start or parse_db_time(p.get('started_at'));date_text=date_base.strftime('%d.%m.%Y') if date_base else 'ohne Datum';first_time=start.strftime('%H:%M Uhr') if start else 'unbekannter Uhrzeit'
 cards=[('🎵','Titel gespielt',len(played)),('🎤','Wünsche',len(requests)),('👍','Upvotes',total_votes),('👥','Wunschgeber',len(requester_counts)),('⏱️','Partydauer',duration_text(duration)),('⏭️','Übersprungen',len(skipped))]
 card_html=''.join(f'<div class="stat"><span>{icon}</span><strong>{safe(value)}</strong><small>{safe(label)}</small></div>' for icon,label,value in cards)
 records=(f'<div class="records"><div><span>🏆 Meiste Wünsche</span><strong>{safe(top_requester[0])}</strong><small>{top_requester[1]} Wünsche</small></div>'
          f'<div><span>🔥 Meiste Upvotes</span><strong>{safe(top_voted["title"]) if top_voted else "–"}</strong><small>{int(top_voted.get("votes") or 0) if top_voted else 0} Votes</small></div>'
          f'<div><span>🎸 Top-Künstler/Kanal</span><strong>{safe(top_artist[0])}</strong><small>{top_artist[1]} Titel</small></div>'
          f'<div><span>📻 Musikmix</span><strong>{len(requests)} Wünsche / {len(bases)} Basis</strong><small>{len(rows)} Titel insgesamt</small></div></div>')
 tracks=[]
 for idx,r in enumerate(rows,1):
  dt=parse_db_time(r.get('started_at') or r.get('created_at'));clock=dt.strftime('%H:%M') if dt else '–';source='Wunsch' if r['source']=='request' else 'Grundplaylist';status='übersprungen' if r['status']=='skipped' else 'gespielt';who=r.get('requested_by') if r['source']=='request' else 'Grundplaylist'
  tracks.append(f'<article class="track"><div class="number">{idx}</div><div class="time">{clock}</div><img src="{safe(r.get("thumbnail"))}" alt=""><div class="track-main"><h3>{safe(r["title"])}</h3><p>{safe(r.get("channel"))}</p><div class="meta"><span>👤 {safe(who)}</span><span>👍 {int(r.get("votes") or 0)}</span><span>🎶 {source}</span><span class="status {status}">{status}</span></div></div><a href="https://www.youtube.com/watch?v={safe(r["video_id"])}" target="_blank" rel="noopener">YouTube ↗</a></article>')
 requester_rows=''.join(f'<li><span>{safe(name)}</span><strong>{count}</strong></li>' for name,count in sorted(requester_counts.items(),key=lambda x:(-x[1],x[0]))[:10]) or '<li><span>Keine Wünsche</span><strong>0</strong></li>'
 return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe(p['name'])} – Party Recap</title><style>
 :root{{--card:#141b2d;--line:#283653;--text:#f8fafc;--muted:#9ca9bf;--blue:#38bdf8;--green:#4ade80}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,#18264a 0,#090d18 38%);color:var(--text);font-family:Inter,system-ui,sans-serif}}main{{max-width:980px;margin:auto;padding:32px 18px 70px}}.hero{{text-align:center;padding:42px 22px;background:linear-gradient(135deg,#172554dd,#3b0764cc);border:1px solid #4c5c88;border-radius:28px;box-shadow:0 18px 60px #0007}}.hero .icon{{font-size:52px}}h1{{font-size:clamp(38px,7vw,72px);margin:8px 0}}.hero p{{max-width:720px;margin:18px auto 0;font-size:19px;line-height:1.65;color:#e2e8f0}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}.stat,.records>div{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px}}.stat span{{font-size:25px}}.stat strong{{display:block;font-size:26px;margin:7px 0}}.stat small,.records small{{color:var(--muted)}}.records{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:20px 0}}.records span,.records strong{{display:block}}.records strong{{font-size:19px;margin:7px 0}}section.panel{{background:#0e1525cc;border:1px solid var(--line);border-radius:22px;padding:20px;margin-top:20px}}.track{{display:grid;grid-template-columns:34px 48px 72px 1fr auto;gap:10px;align-items:center;padding:13px 0;border-top:1px solid #26334d}}.track:first-of-type{{border-top:0}}.track img{{width:72px;aspect-ratio:16/9;object-fit:cover;border-radius:9px;background:#111827}}.track h3{{margin:0 0 4px;font-size:17px}}.track p{{margin:0;color:var(--muted)}}.number,.time{{color:var(--blue);font-weight:700}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;font-size:12px}}.meta span{{background:#1f2937;padding:4px 8px;border-radius:99px}}.status.gespielt{{color:var(--green)}}.status.übersprungen{{color:#fca5a5}}a{{color:var(--blue);text-decoration:none;font-weight:700}}.ranking{{list-style:none;padding:0;margin:0}}.ranking li{{display:flex;justify-content:space-between;padding:10px;border-top:1px solid var(--line)}}footer{{text-align:center;color:var(--muted);margin-top:34px}}@media(max-width:700px){{.stats{{grid-template-columns:repeat(2,1fr)}}.records{{grid-template-columns:1fr}}.track{{grid-template-columns:30px 42px 1fr}}.track img{{display:none}}.track-main,.track>a{{grid-column:3}}}}@media print{{body{{background:#fff;color:#111}}.hero,.stat,.records>div,section.panel{{box-shadow:none;background:#fff;color:#111;border-color:#bbb}}.hero p,.track p,.stat small,.records small,footer{{color:#444}}}}
 </style></head><body><main><header class="hero"><div class="icon">🎉</div><h1>{safe(p['name'])}</h1><p>Hier ist die Playlist unserer <strong>{safe(p['name'])}</strong> vom <strong>{date_text}</strong>.<br>Losgelegt haben wir um <strong>{first_time}</strong> und <strong>{duration_text(duration)}</strong> durchgehalten.<br>Danke für den schönen Abend! 🍻🎵</p></header><div class="stats">{card_html}</div>{records}<section class="panel"><h2>🏅 Wunschgeber-Ranking</h2><ol class="ranking">{requester_rows}</ol></section><section class="panel"><h2>🎶 Unsere Playlist</h2>{''.join(tracks) if tracks else '<p>Noch keine gespielten Titel vorhanden.</p>'}</section><footer>Erstellt mit SmartTube PartyQueue · Party Recap V2.7</footer></main></body></html>"""

@app.get('/api/party/{pid}/export/{fmt}')
async def export(pid:int,fmt:str,password:str='',x_admin_password:str=Header(default='')):
 au(x_admin_password or password)
 with conn() as c:
  p_row=c.execute('SELECT * FROM parties WHERE id=?',(pid,)).fetchone()
  if not p_row:raise HTTPException(404,'Party nicht gefunden')
  p=dict(p_row);rows=[dict(r) for r in c.execute("SELECT created_at,started_at,finished_at,title,channel,thumbnail,duration_seconds,video_id,source,requested_by,votes,target_tv,status FROM queue WHERE party_id=? AND status IN ('played','skipped') ORDER BY COALESCE(started_at,created_at),id",(pid,))]
 if fmt=='json':return StreamingResponse(io.BytesIO(json.dumps({'party':p,'tracks':rows},ensure_ascii=False,indent=2).encode()),media_type='application/json')
 if fmt=='csv':
  o=io.StringIO();fields=rows[0].keys() if rows else ['title'];w=csv.DictWriter(o,fieldnames=fields);w.writeheader();w.writerows(rows);return StreamingResponse(io.BytesIO(o.getvalue().encode('utf-8-sig')),media_type='text/csv')
 if fmt=='m3u':return PlainTextResponse('#EXTM3U\n'+''.join(f"#EXTINF:-1,{r['title']}\nhttps://www.youtube.com/watch?v={r['video_id']}\n" for r in rows))
 if fmt=='html':return HTMLResponse(party_recap_html(p,rows))
 raise HTTPException(400,'Format unbekannt')

