import asyncio,csv,html,io,json,logging,random,secrets,time,re
from xml.sax.saxutils import escape as xml_escape
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import httpx
from fastapi import FastAPI,Header,HTTPException,WebSocket,WebSocketDisconnect,UploadFile,File
from fastapi.responses import FileResponse,HTMLResponse,PlainTextResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from .config import settings
from .db import conn,init_db
from .storage import list_tvs,get_tv,save_tv,delete_tv,default_tv,all_settings,set_settings,apply_runtime_settings,set_default_tv,set_tv_enabled
from .youtube import video_id,details,search,playlist,quota
clients=set();locks={};pb={};guard={};idle={};play_pending={};adb_monitor_task=None
def devices(enabled_only=True):return list_tvs(enabled_only)
log=logging.getLogger('partyqueue.playback');diag=deque(maxlen=500);diag_seq=0
def debug_event(kind,tv=None,**data):
 global diag_seq
 diag_seq+=1
 event={'seq':diag_seq,'time':datetime.now(ZoneInfo(settings.tz)).isoformat(timespec='milliseconds'),'kind':kind,'tv':tv,**data}
 diag.append(event);log.info('[PLAYBACK_DEBUG] %s',json.dumps(event,ensure_ascii=False,default=str));return event
def current_diag():
 now=time.monotonic();out={}
 for d in devices():
  tv=d['id'];x=pb.get(tv,{})
  out[tv]={'name':d['name'],'state':x.get('state'),'position':x.get('media_position'),'app_id':x.get('app_id'),'source':x.get('source'),'age_seconds':round(now-x.get('received',now),3) if x else None,'guard_remaining':round(max(0,guard.get(tv,0)-now),3),'idle_pending':bool(tv in idle and not idle[tv].done())}
 return out
def arm_start_guard(tv,reason):
 guard[tv]=time.monotonic()+settings.prestart_idle_guard
 previous=pb.pop(tv,None)
 task=idle.pop(tv,None)
 cancelled=bool(task and not task.done())
 if cancelled:task.cancel()
 debug_event('START_GUARD_ARMED',tv,reason=reason,seconds=settings.prestart_idle_guard,previous_state=previous.get('state') if previous else None,previous_position=previous.get('media_position') if previous else None,idle_timer_cancelled=cancelled)
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
class TvConfig(BaseModel):
 id:str;name:str;host:str='';enabled:bool=True;is_default:bool=False;ha_entity:str='';connection_mode:str='ha'
class RuntimeSettingsPatch(BaseModel):
 values:dict
class TvEnabledPatch(BaseModel):enabled:bool
class AdbPairRequest(BaseModel):
 host:str;pair_port:int;pair_code:str
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
def pub(p):return {**p,'allowed_devices':[x for x in devices() if x['id'] in allow(p)]}
async def state():
 p=party()
 with conn() as c:
  pls=[dict(r) for r in c.execute('SELECT p.*,COUNT(i.id) item_count FROM playlists p LEFT JOIN playlist_items i ON i.playlist_id=p.id GROUP BY p.id ORDER BY p.name')]
  if not p:return {'party':None,'devices':[],'all_devices':devices(),'playlists':pls,'queue':[],'current':{},'history':[],'playback':{},'quota':quota()}
  q=[dict(r) for r in c.execute("SELECT queue.*,(SELECT COUNT(*) FROM hype_votes hv WHERE hv.queue_id=queue.id) hypes FROM queue WHERE party_id=? AND status='queued' ORDER BY admin_priority DESC,CASE WHEN ?=1 THEN votes END DESC,position,id",(p['id'],p['upvote_sort']))];cu=[dict(r) for r in c.execute("SELECT queue.*,(SELECT COUNT(*) FROM hype_votes hv WHERE hv.queue_id=queue.id) hypes FROM queue WHERE party_id=? AND status='playing'",(p['id'],))];hi=[dict(r) for r in c.execute("SELECT queue.*,(SELECT COUNT(*) FROM hype_votes hv WHERE hv.queue_id=queue.id) hypes FROM queue WHERE party_id=? AND status IN ('played','skipped') ORDER BY finished_at DESC LIMIT 100",(p['id'],))]
 cm={x['target_tv']:x for x in cu};now=time.monotonic();play={}
 for tv,x in pb.items():
  pos=x['media_position']+(max(0,now-x['received']) if x['state']=='playing' else 0);du=float(cm.get(tv,{}).get('duration_seconds')or 0);play[tv]={**x,'media_position':min(pos,du) if du else pos}
 return {'party':pub(p),'devices':pub(p)['allowed_devices'],'all_devices':devices(),'playlists':pls,'queue':q,'current':cm,'history':hi,'playback':play,'quota':quota()}
async def cast():
 s=await state();dead=[]
 for w in clients:
  try:await w.send_json(s)
  except:dead.append(w)
 for w in dead:clients.discard(w)
def adb_target(host):
 host=(host or '').strip()
 if not host:return None
 return host if ':' in host else host+':5555'

async def run_adb(*args,timeout=12):
 proc=await asyncio.create_subprocess_exec('adb',*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
 try:out,_=await asyncio.wait_for(proc.communicate(),timeout=timeout)
 except asyncio.TimeoutError:
  try:proc.kill()
  except:pass
  raise
 return proc.returncode,out.decode(errors='replace').strip()

async def send_play_ha(x,attempt):
 debug_event('PLAY_REQUEST',x['target_tv'],transport='ha',queue_id=x.get('id'),video_id=x.get('video_id'),title=x.get('title'),source=x.get('source'),attempt=attempt)
 try:
  async with httpx.AsyncClient(timeout=settings.play_webhook_timeout) as c:
   r=await asyncio.wait_for(c.post(f"{settings.ha_url.rstrip('/')}/api/webhook/{settings.ha_webhook_id}",json={'url':f"https://www.youtube.com/watch?v={x['video_id']}",'target_tv':x['target_tv'],'smarttube_package':settings.smarttube_package}),timeout=settings.play_webhook_timeout)
   r.raise_for_status()
  debug_event('PLAY_WEBHOOK_OK',x['target_tv'],queue_id=x.get('id'),status_code=r.status_code,attempt=attempt);return True
 except asyncio.TimeoutError:
  debug_event('PLAY_WEBHOOK_TIMEOUT',x['target_tv'],queue_id=x.get('id'),timeout=settings.play_webhook_timeout,attempt=attempt);return False
 except Exception as e:
  debug_event('PLAY_WEBHOOK_ERROR',x['target_tv'],queue_id=x.get('id'),error=repr(e),attempt=attempt);return False

async def send_play_adb(x,tv,attempt):
 target=adb_target(tv.get('ip_address'))
 debug_event('PLAY_REQUEST',x['target_tv'],transport='adb',host=target,queue_id=x.get('id'),video_id=x.get('video_id'),title=x.get('title'),source=x.get('source'),attempt=attempt)
 if not target:
  debug_event('PLAY_ADB_ERROR',x['target_tv'],queue_id=x.get('id'),attempt=attempt,error='Kein Host eingetragen');return False
 try:
  connect_code,connect_out=await run_adb('connect',target,timeout=settings.play_webhook_timeout)
  if connect_code!=0 or ('connected to' not in connect_out.lower() and 'already connected' not in connect_out.lower()):
   debug_event('PLAY_ADB_ERROR',x['target_tv'],queue_id=x.get('id'),attempt=attempt,stage='connect',output=connect_out);return False
  url=f"https://www.youtube.com/watch?v={x['video_id']}"
  code,out=await run_adb('-s',target,'shell','am','start','-a','android.intent.action.VIEW','-d',url,settings.smarttube_package,timeout=settings.play_webhook_timeout)
  ok=code==0
  debug_event('PLAY_ADB_OK' if ok else 'PLAY_ADB_ERROR',x['target_tv'],queue_id=x.get('id'),attempt=attempt,host=target,output=out)
  return ok
 except asyncio.TimeoutError:
  debug_event('PLAY_ADB_TIMEOUT',x['target_tv'],queue_id=x.get('id'),attempt=attempt,timeout=settings.play_webhook_timeout);return False
 except FileNotFoundError:
  debug_event('PLAY_ADB_ERROR',x['target_tv'],queue_id=x.get('id'),attempt=attempt,error='ADB ist nicht installiert');return False
 except Exception as e:
  debug_event('PLAY_ADB_ERROR',x['target_tv'],queue_id=x.get('id'),attempt=attempt,error=repr(e));return False

async def send_play_command(x,attempt):
 tv=get_tv(x['target_tv'])
 if not tv:
  debug_event('PLAY_TRANSPORT_ERROR',x['target_tv'],queue_id=x.get('id'),attempt=attempt,error='TV nicht gefunden');return False
 return await send_play_adb(x,tv,attempt) if tv.get('connection_mode')=='adb' else await send_play_ha(x,attempt)

async def play_watchdog(tv,queue_id,x):
 try:
  debug_event('PLAY_CONFIRM_WAIT',tv,queue_id=queue_id,timeout=settings.play_confirm_timeout)
  await asyncio.sleep(settings.play_confirm_timeout)
  pending=play_pending.get(tv)
  if not pending or pending['queue_id']!=queue_id:return
  arm_start_guard(tv,'play_retry');debug_event('PLAY_RETRY',tv,queue_id=queue_id,video_id=x.get('video_id'),title=x.get('title'))
  await send_play_command(x,2)
  await asyncio.sleep(settings.play_retry_timeout)
  pending=play_pending.get(tv)
  if pending and pending['queue_id']==queue_id:
   debug_event('PLAY_CONFIRM_FAILED',tv,queue_id=queue_id,video_id=x.get('video_id'),title=x.get('title'))
   play_pending.pop(tv,None);await cast()
 except asyncio.CancelledError:pass

async def play(x):
 tv=x['target_tv'];old=play_pending.pop(tv,None)
 if old and old.get('task') and not old['task'].done():old['task'].cancel()
 arm_start_guard(tv,'play_request')
 pending={'queue_id':x['id'],'video_id':x.get('video_id'),'task':None,'requested':time.monotonic()};play_pending[tv]=pending
 pending['task']=asyncio.create_task(play_watchdog(tv,x['id'],dict(x)))
 asyncio.create_task(send_play_command(dict(x),1));debug_event('PLAY_DISPATCHED',tv,queue_id=x['id'],attempt=1)

def base(c,p,tv):
 if not p['playlist_enabled'] or not p['playlist_id']:return None
 a=[dict(r) for r in c.execute('SELECT * FROM playlist_items WHERE playlist_id=? AND enabled=1',(p['playlist_id'],))]
 if not a:return None
 used=[r['playlist_item_id'] for r in c.execute('SELECT playlist_item_id FROM base_play_history WHERE party_id=? AND target_tv=? ORDER BY id DESC LIMIT ?',(p['id'],tv,settings.base_playlist_recent_exclude))];x=random.choice([z for z in a if z['id'] not in used]or a);c.execute('INSERT INTO base_play_history(target_tv,playlist_item_id,party_id) VALUES(?,?,?)',(tv,x['id'],p['id']));return x
async def nxt(tv):
 p=party();tv=tvok(tv,p);debug_event('NEXT_ENTER',tv,party_id=p['id']);l=locks.setdefault(tv,asyncio.Lock())
 async with l:
  with conn() as c:
   if c.execute("SELECT 1 FROM queue WHERE party_id=? AND target_tv=? AND status='playing'",(p['id'],tv)).fetchone():debug_event('NEXT_BLOCKED_PLAYING',tv,party_id=p['id']);return False
   r=c.execute("SELECT * FROM queue WHERE party_id=? AND target_tv=? AND status='queued' ORDER BY admin_priority DESC,CASE WHEN ?=1 THEN votes END DESC,position,id LIMIT 1",(p['id'],tv,p['upvote_sort'])).fetchone()
   if r:x=dict(r);c.execute("UPDATE queue SET status='playing',started_at=CURRENT_TIMESTAMP WHERE id=?",(x['id'],));debug_event('NEXT_QUEUE_SELECTED',tv,queue_id=x['id'],video_id=x['video_id'],title=x['title'],votes=x.get('votes'),position=x.get('position'))
   else:
    b=base(c,p,tv)
    if not b:debug_event('NEXT_NO_ITEM',tv,party_id=p['id']);return False
    k=c.execute("INSERT INTO queue(video_id,title,channel,thumbnail,duration_seconds,requested_by,target_tv,position,source,status,party_id,playlist_id,started_at) VALUES(?,?,?,?,?,'Grundplaylist',?,0,'base','playing',?,?,CURRENT_TIMESTAMP)",(b['video_id'],b['title'],b['channel'],b['thumbnail'],b['duration_seconds'],tv,p['id'],p['playlist_id']));x={**b,'id':k.lastrowid,'target_tv':tv,'source':'base'};debug_event('NEXT_BASE_SELECTED',tv,queue_id=x['id'],video_id=x['video_id'],title=x['title'],duration=x.get('duration_seconds'))
  await play(x);await cast();return True
async def done(tv,st='played',reason='unspecified'):
 p=party();tv=tvok(tv,p)
 with conn() as c:
  current=c.execute("SELECT id,video_id,title,duration_seconds,started_at FROM queue WHERE party_id=? AND target_tv=? AND status='playing'",(p['id'],tv)).fetchone()
  n=c.execute("UPDATE queue SET status=?,finished_at=CURRENT_TIMESTAMP WHERE party_id=? AND target_tv=? AND status='playing'",(st,p['id'],tv)).rowcount
 debug_event('DONE',tv,reason=reason,result_status=st,updated=n,queue_id=current['id'] if current else None,video_id=current['video_id'] if current else None,title=current['title'] if current else None,duration=current['duration_seconds'] if current else None)
 if n:
  arm_start_guard(tv,'done_'+reason)
  await cast();await nxt(tv)
async def metadata(v=None,u=None):
 v=v or video_id(u or'');a=await details([v]) if v else[]
 if not a:raise HTTPException(400,'Video nicht verfügbar')
 return a[0]
def parse_adb_media_session(output,package,device_uptime=None):
 blocks=re.split(r'(?=MediaSessionRecord\{)',output)
 candidates=[b for b in blocks if package in b]
 if not candidates:return {'state':'idle','media_position':0,'app_id':None}
 def parse_block(block):
  playback=re.search(r'PlaybackState\s*\{\s*state=(?:(?P<name>[A-Z_]+)\()?(?P<code>\d+)\)?,\s*position=(?P<position>-?\d+).*?speed=(?P<speed>-?[0-9.]+).*?updated=(?P<updated>\d+)',block,re.IGNORECASE)
  if not playback:return None
  code=int(playback.group('code'));base_ms=max(0,int(playback.group('position')));speed=float(playback.group('speed'));updated_ms=int(playback.group('updated'))
  state={3:'playing',2:'paused',6:'buffering',8:'connecting'}.get(code,'idle')
  position_ms=base_ms
  if state=='playing' and device_uptime is not None and speed>0:
   position_ms+=max(0,device_uptime*1000-updated_ms)*speed
  return {'state':state,'media_position':position_ms/1000,'app_id':package,'_code':code,'_base_position':base_ms/1000,'_updated':updated_ms,'_speed':speed}
 parsed=[(b,parse_block(b)) for b in candidates]
 parsed=[(b,x) for b,x in parsed if x]
 if not parsed:return {'state':'idle','media_position':0,'app_id':package}
 block,data=max(parsed,key=lambda item:(item[1]['state'] in ('playing','paused','buffering','connecting'),'active=true' in item[0].lower(),len(item[0])))
 for key in ('_code','_base_position','_updated','_speed'):data.pop(key,None)
 return data

async def poll_adb_tv(tv):
 target=adb_target(tv.get('ip_address'))
 if not target:return
 try:
  code,uptime_out=await run_adb('-s',target,'shell','cat','/proc/uptime',timeout=max(3,settings.adb_poll_interval))
  if code!=0:
   debug_event('ADB_POLL_ERROR',tv['id'],host=target,stage='uptime',output=uptime_out);return
  try:device_uptime=float(uptime_out.split()[0])
  except (ValueError,IndexError):
   debug_event('ADB_POLL_ERROR',tv['id'],host=target,stage='uptime_parse',output=uptime_out);return
  code,out=await run_adb('-s',target,'shell','dumpsys','media_session',timeout=max(3,settings.adb_poll_interval))
  if code!=0:
   debug_event('ADB_POLL_ERROR',tv['id'],host=target,stage='media_session',output=out);return
  data=parse_adb_media_session(out,settings.smarttube_package,device_uptime)
  old=pb.get(tv['id'],{})
  changed=data['state']!=old.get('state') or abs(data['media_position']-float(old.get('media_position',0) or 0))>=0.5 or data['app_id']!=old.get('app_id')
  if changed:await process_progress(Progress(target_tv=tv['id'],**data),source='adb')
 except asyncio.TimeoutError:debug_event('ADB_POLL_TIMEOUT',tv['id'],host=target)
 except Exception as e:debug_event('ADB_POLL_ERROR',tv['id'],host=target,error=repr(e))

async def adb_monitor_loop():
 debug_event('ADB_MONITOR_STARTED',interval=settings.adb_poll_interval)
 try:
  while True:
   tvs=[tv for tv in list_tvs(True) if tv.get('connection_mode')=='adb' and tv.get('ip_address')]
   if tvs:await asyncio.gather(*(poll_adb_tv(tv) for tv in tvs))
   await asyncio.sleep(max(0.5,settings.adb_poll_interval))
 except asyncio.CancelledError:debug_event('ADB_MONITOR_STOPPED')

@asynccontextmanager
async def life(app):
 global adb_monitor_task
 init_db();apply_runtime_settings(settings);adb_monitor_task=asyncio.create_task(adb_monitor_loop())
 try:yield
 finally:
  if adb_monitor_task:
   adb_monitor_task.cancel()
   try:await adb_monitor_task
   except asyncio.CancelledError:pass

app=FastAPI(version='3.0.0-beta2',lifespan=life);B=Path(__file__).parent;BANNERS = Path(settings.data_dir) / 'banners'
BANNERS.mkdir(parents=True,exist_ok=True);app.mount("/banners",StaticFiles(directory=BANNERS),name="banners");app.mount('/static',StaticFiles(directory=B/'static'),name='static')
@app.get('/')
async def g():return FileResponse(B/'static/guest.html')
@app.get('/host')
async def h():return FileResponse(B/'static/host.html')
@app.get('/api/health')
async def health():return {'ok':True,'version':'3.0.0-beta2'}
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
 b.requested_by=b.requested_by.strip()
 if not b.requested_by or b.requested_by.lower()=='gast':raise HTTPException(400,'Bitte zuerst einen Namen angeben')
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
@app.post('/api/queue/{qid}/hype')
async def hype(qid:int,b:Vote):
 if not b.guest_id.strip():raise HTTPException(400,'Gast-ID fehlt')
 with conn() as c:
  row=c.execute("SELECT id,status FROM queue WHERE id=?",(qid,)).fetchone()
  if not row or row['status']!='playing':raise HTTPException(409,'Titel läuft nicht mehr')
  old=c.execute('SELECT 1 FROM hype_votes WHERE queue_id=? AND guest_id=?',(qid,b.guest_id)).fetchone()
  c.execute('DELETE FROM hype_votes WHERE queue_id=? AND guest_id=?',(qid,b.guest_id)) if old else c.execute('INSERT INTO hype_votes VALUES(?,?,CURRENT_TIMESTAMP)',(qid,b.guest_id))
  total=c.execute('SELECT COUNT(*) n FROM hype_votes WHERE queue_id=?',(qid,)).fetchone()['n']
 await cast();return {'hyped':not bool(old),'hype_total':total}

@app.post('/api/admin/login')
async def login(b:Auth):au(b.password);return {'ok':True}
@app.get('/api/admin/tvs')
async def admin_tvs(x_admin_password:str=Header(default='')):au(x_admin_password);return list_tvs(False)
@app.post('/api/admin/tvs')
async def admin_tv_create(b:TvConfig,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 try:r=save_tv(b.model_dump())
 except ValueError as e:raise HTTPException(400,str(e))
 await cast();return r
@app.patch('/api/admin/tvs/{tv_id}')
async def admin_tv_patch(tv_id:str,b:TvConfig,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 try:r=save_tv(b.model_dump(),tv_id)
 except ValueError as e:raise HTTPException(400,str(e))
 await cast();return r
@app.delete('/api/admin/tvs/{tv_id}')
async def admin_tv_delete(tv_id:str,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 try:delete_tv(tv_id)
 except ValueError as e:raise HTTPException(409,str(e))
 await cast();return {'ok':True}
@app.post('/api/admin/tvs/{tv_id}/default')
async def admin_tv_default(tv_id:str,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 try:r=set_default_tv(tv_id)
 except ValueError as e:raise HTTPException(409,str(e))
 await cast();return r
@app.patch('/api/admin/tvs/{tv_id}/enabled')
async def admin_tv_enabled(tv_id:str,b:TvEnabledPatch,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 try:r=set_tv_enabled(tv_id,b.enabled)
 except ValueError as e:raise HTTPException(409,str(e))
 await cast();return r
@app.post('/api/admin/tvs/{tv_id}/adb-test')
async def admin_tv_adb_test(tv_id:str,x_admin_password:str=Header(default='')):
 au(x_admin_password);tv=get_tv(tv_id)
 if not tv:raise HTTPException(404,'TV nicht gefunden')
 host=(tv.get('ip_address') or '').strip()
 if not host:raise HTTPException(400,'Kein Host eingetragen')
 if not re.fullmatch(r'[A-Za-z0-9._:-]+',host):raise HTTPException(400,'Host enthält ungültige Zeichen')
 target=host if ':' in host else host+':5555'
 try:
  proc=await asyncio.create_subprocess_exec('adb','connect',target,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
  out,_=await asyncio.wait_for(proc.communicate(),timeout=12);text=out.decode(errors='replace').strip()
 except asyncio.TimeoutError:
  try:proc.kill()
  except:pass
  raise HTTPException(504,'ADB-Verbindung hat das Zeitlimit überschritten')
 except FileNotFoundError:raise HTTPException(500,'ADB ist im Container nicht installiert')
 ok=proc.returncode==0 and ('connected to' in text.lower() or 'already connected' in text.lower())
 debug_event('ADB_TEST',tv_id,host=target,ok=ok,output=text)
 return {'ok':ok,'host':target,'output':text}
@app.post('/api/admin/adb/pair')
async def admin_adb_pair(b:AdbPairRequest,x_admin_password:str=Header(default='')):
 au(x_admin_password);host=b.host.strip();code=b.pair_code.strip()
 if not re.fullmatch(r'[A-Za-z0-9._:-]+',host):raise HTTPException(400,'Host enthält ungültige Zeichen')
 if not 1<=b.pair_port<=65535:raise HTTPException(400,'Pairing-Port ist ungültig')
 if not re.fullmatch(r'\d{6}',code):raise HTTPException(400,'Pairing-Code muss aus 6 Ziffern bestehen')
 pair_target=f'{host}:{b.pair_port}'
 try:
  rc,out=await run_adb('pair',pair_target,code,timeout=20)
 except asyncio.TimeoutError:raise HTTPException(504,'ADB-Pairing hat das Zeitlimit überschritten')
 except FileNotFoundError:raise HTTPException(500,'ADB ist im Container nicht installiert')
 ok=rc==0 and ('successfully paired' in out.lower() or 'already paired' in out.lower())
 debug_event('ADB_PAIR',host=pair_target,ok=ok,output=out)
 if not ok:raise HTTPException(409,out or 'ADB-Pairing fehlgeschlagen')
 return {'ok':True,'host':pair_target,'output':out}
@app.post('/api/admin/adb/connect')
async def admin_adb_connect(b:AdbPairRequest,x_admin_password:str=Header(default='')):
 au(x_admin_password);host=b.host.strip()
 if not re.fullmatch(r'[A-Za-z0-9._:-]+',host):raise HTTPException(400,'Host enthält ungültige Zeichen')
 target=adb_target(host)
 try:rc,out=await run_adb('connect',target,timeout=12)
 except asyncio.TimeoutError:raise HTTPException(504,'ADB-Verbindung hat das Zeitlimit überschritten')
 except FileNotFoundError:raise HTTPException(500,'ADB ist im Container nicht installiert')
 ok=rc==0 and ('connected to' in out.lower() or 'already connected' in out.lower())
 debug_event('ADB_CONNECT',host=target,ok=ok,output=out)
 if not ok:raise HTTPException(409,out or 'ADB-Verbindung fehlgeschlagen')
 return {'ok':True,'host':target,'output':out}
@app.post('/api/admin/party/banner')
async def party_banner_upload(banner:UploadFile=File(...),x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party()
 if not p:raise HTTPException(409,'Es läuft keine Party')
 ext={'.jpg':'.jpg','.jpeg':'.jpg','.png':'.png','.webp':'.webp'}.get(Path(banner.filename or '').suffix.lower())
 if not ext or banner.content_type not in {'image/jpeg','image/png','image/webp'}:raise HTTPException(400,'Erlaubt sind JPG, PNG und WebP')
 data=await banner.read(5*1024*1024+1)
 if len(data)>5*1024*1024:raise HTTPException(413,'Banner darf maximal 5 MB groß sein')
 if not data:raise HTTPException(400,'Bannerdatei ist leer')
 name=f'party_{p["id"]}{ext}';target=BANNERS/name
 for candidate in BANNERS.glob(f'party_{p["id"]}.*'):
  if candidate!=target:candidate.unlink(missing_ok=True)
 target.write_bytes(data)
 with conn() as c:c.execute('UPDATE parties SET banner_path=? WHERE id=?',(f'/banners/{name}',p['id']))
 await cast();return {'ok':True,'banner_path':f'/banners/{name}'}
@app.delete('/api/admin/party/banner')
async def party_banner_delete(x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party()
 if not p:raise HTTPException(409,'Es läuft keine Party')
 for candidate in BANNERS.glob(f'party_{p["id"]}.*'):candidate.unlink(missing_ok=True)
 with conn() as c:c.execute("UPDATE parties SET banner_path='' WHERE id=?",(p['id'],))
 await cast();return {'ok':True}
@app.get('/api/admin/settings')
async def admin_settings(x_admin_password:str=Header(default='')):au(x_admin_password);return all_settings()
@app.patch('/api/admin/settings')
async def admin_settings_patch(b:RuntimeSettingsPatch,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 try:r=set_settings(b.values);apply_runtime_settings(settings)
 except (ValueError,TypeError) as e:raise HTTPException(400,str(e))
 await cast();return r
@app.post('/api/admin/start')
async def start(b:Tv,x_admin_password:str=Header(default='')):au(x_admin_password);return {'started':await nxt(b.target_tv)}
@app.post('/api/admin/skip')
async def skip(b:Tv,x_admin_password:str=Header(default='')):au(x_admin_password);debug_event('MANUAL_SKIP_BUTTON',b.target_tv);await done(b.target_tv,'skipped','host_button');return {'ok':True}
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

def close_party(c,p):
 if not p:return
 c.execute("UPDATE queue SET status='played',finished_at=COALESCE(finished_at,CURRENT_TIMESTAMP) WHERE party_id=? AND status='playing'",(p['id'],))
 c.execute("UPDATE queue SET status='cancelled',finished_at=COALESCE(finished_at,CURRENT_TIMESTAMP) WHERE party_id=? AND status='queued'",(p['id'],))
 c.execute("UPDATE parties SET active=0,queue_locked=1,ended_at=COALESCE(ended_at,CURRENT_TIMESTAMP) WHERE id=?",(p['id'],))

@app.get('/api/admin/parties')
async def party_archive(x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:return [dict(r) for r in c.execute("""
 SELECT p.id,p.name,p.active,p.started_at,p.ended_at,
  COUNT(CASE WHEN q.status IN ('played','skipped') THEN 1 END) played_total,
  COALESCE(SUM(CASE WHEN q.source='request' AND q.status IN ('played','skipped') THEN 1 ELSE 0 END),0) request_total,
  COALESCE(SUM(CASE WHEN q.status IN ('played','skipped') THEN q.votes ELSE 0 END),0) votes_total,
  (SELECT requested_by FROM queue qr WHERE qr.party_id=p.id AND qr.source='request' AND qr.status IN ('played','skipped') GROUP BY requested_by ORDER BY COUNT(*) DESC,requested_by LIMIT 1) top_requester,
  (SELECT COUNT(*) FROM queue qr WHERE qr.party_id=p.id AND qr.source='request' AND qr.status IN ('played','skipped') AND qr.requested_by=(SELECT requested_by FROM queue qrr WHERE qrr.party_id=p.id AND qrr.source='request' AND qrr.status IN ('played','skipped') GROUP BY requested_by ORDER BY COUNT(*) DESC,requested_by LIMIT 1)) top_requester_count,
  (SELECT channel FROM queue qa WHERE qa.party_id=p.id AND qa.status IN ('played','skipped') AND COALESCE(qa.channel,'')<>'' GROUP BY channel ORDER BY COUNT(*) DESC,channel LIMIT 1) top_artist,
  (SELECT COUNT(*) FROM queue qa WHERE qa.party_id=p.id AND qa.status IN ('played','skipped') AND qa.channel=(SELECT channel FROM queue qaa WHERE qaa.party_id=p.id AND qaa.status IN ('played','skipped') AND COALESCE(qaa.channel,'')<>'' GROUP BY channel ORDER BY COUNT(*) DESC,channel LIMIT 1)) top_artist_count,
  (SELECT title FROM queue qv WHERE qv.party_id=p.id AND qv.status IN ('played','skipped') ORDER BY votes DESC,title LIMIT 1) top_voted_title,
  COALESCE((SELECT votes FROM queue qv WHERE qv.party_id=p.id AND qv.status IN ('played','skipped') ORDER BY votes DESC,title LIMIT 1),0) top_voted_votes,
  (SELECT title FROM queue qh WHERE qh.party_id=p.id AND qh.status IN ('played','skipped') ORDER BY (SELECT COUNT(*) FROM hype_votes hv WHERE hv.queue_id=qh.id) DESC,title LIMIT 1) top_hype_title,
  COALESCE((SELECT COUNT(*) FROM hype_votes hv WHERE hv.queue_id=(SELECT id FROM queue qh WHERE qh.party_id=p.id AND qh.status IN ('played','skipped') ORDER BY (SELECT COUNT(*) FROM hype_votes hv2 WHERE hv2.queue_id=qh.id) DESC,title LIMIT 1)),0) top_hype_votes
 FROM parties p LEFT JOIN queue q ON q.party_id=p.id
 GROUP BY p.id ORDER BY p.started_at DESC,p.id DESC
 """)]

@app.delete('/api/admin/parties/{pid}')
async def party_delete(pid:int,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 with conn() as c:
  p=c.execute('SELECT id,name,active FROM parties WHERE id=?',(pid,)).fetchone()
  if not p:raise HTTPException(404,'Party nicht gefunden')
  if p['active']:raise HTTPException(409,'Die aktive Party kann nicht gelöscht werden')
  qids=[r['id'] for r in c.execute('SELECT id FROM queue WHERE party_id=?',(pid,))]
  if qids:
   ph=','.join('?' for _ in qids);c.execute(f'DELETE FROM votes WHERE queue_id IN ({ph})',qids);c.execute(f'DELETE FROM hype_votes WHERE queue_id IN ({ph})',qids)
  c.execute('DELETE FROM base_play_history WHERE party_id=?',(pid,))
  c.execute('DELETE FROM queue WHERE party_id=?',(pid,))
  c.execute('DELETE FROM parties WHERE id=?',(pid,))
 return {'ok':True,'id':pid,'name':p['name']}

@app.post('/api/admin/party/close')
async def party_close(x_admin_password:str=Header(default='')):
 au(x_admin_password);p=party()
 if not p:raise HTTPException(409,'Es läuft keine Party')
 with conn() as c:close_party(c,p)
 pb.clear();guard.clear()
 for item in play_pending.values():
  if item.get('task') and not item['task'].done():item['task'].cancel()
 play_pending.clear()
 for task in idle.values():
  if not task.done():task.cancel()
 idle.clear();await cast();return {'ok':True,'party_id':p['id']}

@app.post('/api/admin/parties')
async def party_create(b:PartyCreate,x_admin_password:str=Header(default='')):
 au(x_admin_password);name=b.name.strip()
 if not name:raise HTTPException(400,'Partyname fehlt')
 current=party()
 if b.clone_current and not current:raise HTTPException(409,'Keine aktive Party zum Klonen vorhanden')
 with conn() as c:
  if current:close_party(c,current)
  if b.clone_current:
   values={k:current[k] for k in ('playlist_id','allowed_devices','default_tv','request_limit','repeat_window','upvote_sort','detect_external_skip','playlist_enabled')}
  else:
   available=devices()
   if not available:raise HTTPException(409,'Bitte zuerst mindestens einen aktiven TV anlegen')
   allowed=b.allowed_devices or [x['id'] for x in available]
   selected_default=b.default_tv or default_tv()
   values={'playlist_id':b.playlist_id or 1,'allowed_devices':','.join(allowed),'default_tv':selected_default,'request_limit':settings.max_requests_per_guest if b.request_limit is None else b.request_limit,'repeat_window':settings.base_playlist_recent_exclude if b.repeat_window is None else b.repeat_window,'upvote_sort':1 if b.upvote_sort is None else int(b.upvote_sort),'detect_external_skip':0 if b.detect_external_skip is None else int(b.detect_external_skip),'playlist_enabled':1 if b.playlist_enabled is None else int(b.playlist_enabled)}
  r=c.execute("INSERT INTO parties(name,playlist_id,allowed_devices,default_tv,request_limit,repeat_window,queue_locked,upvote_sort,detect_external_skip,playlist_enabled,active,started_at,ended_at) VALUES(?,?,?,?,?,?,0,?,?,?,?,CURRENT_TIMESTAMP,NULL)",(name,values['playlist_id'],values['allowed_devices'],values['default_tv'],values['request_limit'],values['repeat_window'],values['upvote_sort'],values['detect_external_skip'],values['playlist_enabled'],1))
 pb.clear();guard.clear()
 for item in play_pending.values():
  if item.get('task') and not item['task'].done():item['task'].cancel()
 play_pending.clear()
 for task in idle.values():
  if not task.done():task.cancel()
 idle.clear();await cast();return {'ok':True,'id':r.lastrowid}
async def process_progress(b:Progress,source='home_assistant'):
 p=party();tv=tvok(b.target_tv,p);now=time.monotonic();old=pb.get(tv,{});old_state=old.get('state');old_pos=float(old.get('media_position',0) or 0);new_pos=max(0,b.media_position);guard_remaining=max(0,guard.get(tv,0)-now)
 pb[tv]={'state':b.state,'media_position':new_pos,'app_id':b.app_id,'received':now,'source':source}
 pending=play_pending.get(tv)
 if pending and b.state in ('playing','buffering') and b.app_id==settings.smarttube_package:
  if new_pos<=settings.play_confirm_max_position:
   play_pending.pop(tv,None)
   if pending.get('task') and not pending['task'].done():pending['task'].cancel()
   debug_event('PLAY_CONFIRMED',tv,queue_id=pending['queue_id'],video_id=pending.get('video_id'),position=round(new_pos,3),latency=round(now-pending['requested'],3),state=b.state)
  else:debug_event('PLAY_CONFIRM_REJECTED',tv,queue_id=pending['queue_id'],position=round(new_pos,3),max_position=settings.play_confirm_max_position,state=b.state)
 with conn() as c:r=c.execute("SELECT * FROM queue WHERE party_id=? AND target_tv=? AND status='playing'",(p['id'],tv)).fetchone()
 duration=float(r['duration_seconds'] or 0) if r else 0;end_threshold=max(0,duration-settings.prestart_seconds) if duration else None
 valid_app=b.app_id==settings.smarttube_package;active_state=b.state in ('playing','buffering');guard_ok=now>=guard.get(tv,0)
 end_match=bool(r and valid_app and active_state and duration and (new_pos>=end_threshold or (duration - new_pos)<=1.0))
 reset_match=bool(r and valid_app and active_state and p['detect_external_skip'] and guard_ok and old_pos>=settings.external_skip_min_previous and new_pos<=settings.external_skip_max_new and new_pos+1<old_pos)
 idle_end=bool(r and b.state=='idle' and (old_pos>=end_threshold or (duration - old_pos)<=1.0)) if end_threshold is not None else False
 idle_skip=bool(r and b.state=='idle' and p['detect_external_skip'] and guard_ok and old_pos>=settings.external_skip_min_previous and not idle_end)
 debug_event('PROGRESS',tv,source=source,state=b.state,old_state=old_state,position=round(new_pos,3),old_position=round(old_pos,3),app_id=b.app_id,expected_app=settings.smarttube_package,skip_enabled=bool(p['detect_external_skip']),guard_remaining=round(guard_remaining,3),queue_id=r['id'] if r else None,video_id=r['video_id'] if r else None,title=r['title'] if r else None,duration=r['duration_seconds'] if r else None)
 if r and valid_app and active_state:
  debug_event('DECISION',tv,end_match=end_match,skip_match=reset_match,skip_enabled=bool(p['detect_external_skip']),state=b.state,old_state=old_state,old_position=round(old_pos,3),new_position=round(new_pos,3),duration=r['duration_seconds'],end_threshold=round(end_threshold,3) if end_threshold is not None else None,old_threshold=settings.external_skip_min_previous,new_threshold=settings.external_skip_max_new,guard_remaining=round(guard_remaining,3))
  if end_match:
   guard[tv]=time.monotonic()+settings.prestart_idle_guard;debug_event('END_DETECTED',tv,position=round(new_pos,3),duration=r['duration_seconds'],state=b.state,new_guard_seconds=settings.prestart_idle_guard);await done(tv,'played','duration_threshold');return {'ok':True}
  if reset_match:
   debug_event('EXTERNAL_SKIP_DETECTED',tv,old_position=round(old_pos,3),new_position=round(new_pos,3),old_state=old_state,new_state=b.state,method='position_reset');await done(tv,'skipped','position_reset');return {'ok':True}
 elif r and b.state=='idle' and idle_end:
  debug_event('END_DETECTED',tv,position=round(old_pos,3),duration=r['duration_seconds'],state='idle',method='idle_after_end');await done(tv,'played','idle_after_end');return {'ok':True}
 elif r and b.state=='idle' and idle_skip:
  debug_event('EXTERNAL_SKIP_DETECTED',tv,old_position=round(old_pos,3),new_position=0,old_state=old_state,new_state='idle',method='idle_before_end');await done(tv,'skipped','idle_before_end');return {'ok':True}
 elif r:
  debug_event('DECISION_SKIPPED',tv,reason='state_or_app_mismatch',state=b.state,app_id=b.app_id,expected_app=settings.smarttube_package,idle_end=idle_end,idle_skip=idle_skip)
 if b.state=='idle' and now>=guard.get(tv,0):
  debug_event('IDLE_TIMER_SCHEDULED',tv,delay=settings.idle_fallback_delay)
  async def f():
   await asyncio.sleep(settings.idle_fallback_delay)
   current_state=pb.get(tv,{}).get('state');remaining=max(0,guard.get(tv,0)-time.monotonic());debug_event('IDLE_TIMER_FIRED',tv,state=current_state,guard_remaining=round(remaining,3))
   if current_state=='idle' and remaining<=0:await done(tv,'played','idle_fallback')
  if tv in idle and not idle[tv].done():idle[tv].cancel();debug_event('IDLE_TIMER_CANCELLED',tv,reason='rescheduled')
  idle[tv]=asyncio.create_task(f())
 elif b.state=='idle':debug_event('IDLE_IGNORED_GUARD',tv,guard_remaining=round(max(0,guard.get(tv,0)-now),3))
 await cast();return {'ok':True}

@app.post('/api/playback/progress')
async def progress(b:Progress,x_admin_password:str=Header(default='')):
 au(x_admin_password)
 tv=get_tv(b.target_tv)
 if tv and tv.get('connection_mode')=='adb':
  debug_event('HA_PROGRESS_IGNORED',b.target_tv,state=b.state,reason='adb_mode');return {'ok':True,'ignored':True}
 return await process_progress(b,'home_assistant')

@app.get('/api/admin/playback-debug')
async def playback_debug(limit:int=200,tv:Optional[str]=None,x_admin_password:str=Header(default='')):
 au(x_admin_password);limit=max(1,min(limit,500));events=list(diag)
 if tv:events=[x for x in events if x.get('tv')==tv]
 return {'version':'3.0.0-beta2','generated_at':datetime.now(ZoneInfo(settings.tz)).isoformat(timespec='seconds'),'devices':current_diag(),'events':events[-limit:]}

@app.delete('/api/admin/playback-debug')
async def playback_debug_clear(x_admin_password:str=Header(default='')):
 au(x_admin_password);diag.clear();debug_event('DEBUG_CLEARED');return {'ok':True}
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
 copied=0;skipped=0
 with conn() as c:
  if not c.execute('SELECT 1 FROM playlists WHERE id=?',(b.target_playlist_id,)).fetchone():raise HTTPException(404,'Zielplaylist nicht gefunden')
  ph=','.join('?' for _ in b.item_ids)
  rows=[dict(r) for r in c.execute(f'SELECT * FROM playlist_items WHERE playlist_id=? AND id IN ({ph})',(b.source_playlist_id,*b.item_ids))]
  if len(rows)!=len(set(b.item_ids)):raise HTTPException(409,'Mindestens ein ausgewählter Titel wurde zwischenzeitlich geändert')
  pos=c.execute('SELECT COALESCE(MAX(position),0) n FROM playlist_items WHERE playlist_id=?',(b.target_playlist_id,)).fetchone()['n']
  for row in sorted(rows,key=lambda x:(x['position'],x['id'])):
   pos+=1
   inserted=c.execute("INSERT OR IGNORE INTO playlist_items(playlist_id,video_id,title,channel,thumbnail,duration_seconds,enabled,position,added_from) VALUES(?,?,?,?,?,?,?,?,?)",(b.target_playlist_id,row['video_id'],row['title'],row['channel'],row['thumbnail'],row['duration_seconds'],row['enabled'],pos,'copy' if b.mode=='copy' else 'move')).rowcount
   copied+=inserted;skipped+=0 if inserted else 1
  if b.mode=='move':c.execute(f'DELETE FROM playlist_items WHERE playlist_id=? AND id IN ({ph})',(b.source_playlist_id,*b.item_ids))
  for playlist_id in {b.source_playlist_id,b.target_playlist_id}:
   ids=[r['id'] for r in c.execute('SELECT id FROM playlist_items WHERE playlist_id=? ORDER BY position,id',(playlist_id,))]
   for position,item_id in enumerate(ids,1):c.execute('UPDATE playlist_items SET position=? WHERE id=?',(position,item_id))
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
def local_time(value):
 if not value:return None
 try:
  d=datetime.fromisoformat(str(value).replace(' ','T'))
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(ZoneInfo(settings.tz))
 except:return None

def duration_text(seconds):
 seconds=max(0,int(seconds or 0));h,rest=divmod(seconds,3600);m=rest//60
 return f'{h} Stunden {m} Minuten' if h else f'{m} Minuten'

def recap_html(p,rows):
 safe=lambda x:html.escape(str(x or''))
 start=next((local_time(r.get('started_at') or r.get('created_at')) for r in rows if local_time(r.get('started_at') or r.get('created_at'))),local_time(p.get('started_at')))
 end=local_time(p.get('ended_at')) or next((local_time(r.get('finished_at')) for r in reversed(rows) if r.get('finished_at')),None) or datetime.now(ZoneInfo(settings.tz))
 seconds=max(0,(end-start).total_seconds()) if start else 0
 played=[r for r in rows if r['status']=='played'];skipped=[r for r in rows if r['status']=='skipped'];requests=[r for r in rows if r['source']=='request'];bases=[r for r in rows if r['source']=='base']
 requesters={};artists={}
 for r in requests:
  n=(r.get('requested_by') or 'Gast').strip() or 'Gast';requesters[n]=requesters.get(n,0)+1
 for r in rows:
  n=(r.get('channel') or 'Unbekannt').strip() or 'Unbekannt';artists[n]=artists.get(n,0)+1
 top_req=max(requesters.items(),key=lambda x:(x[1],x[0])) if requesters else ('–',0);top_artist=max(artists.items(),key=lambda x:(x[1],x[0])) if artists else ('–',0);top_vote=max(rows,key=lambda r:(r.get('votes') or 0,r.get('title') or''),default=None);votes=sum(int(r.get('votes') or 0) for r in rows);hypes=sum(int(r.get('hypes') or 0) for r in rows);top_hype=max(rows,key=lambda r:(r.get('hypes') or 0,r.get('title') or''),default=None)
 date=(start or local_time(p.get('started_at')));date_text=date.strftime('%d.%m.%Y') if date else 'ohne Datum';start_text=start.strftime('%H:%M Uhr') if start else 'unbekannter Uhrzeit'
 cards=[('🎵','Titel gespielt',len(played)),('🎤','Wünsche',len(requests)),('👍','Upvotes',votes),('👥','Wunschgeber',len(requesters)),('⏱️','Partydauer',duration_text(seconds)),('⏭️','Übersprungen',len(skipped)),('🔥','Hypes',hypes)]
 cards_html=''.join(f'<div class="stat"><span>{i}</span><strong>{safe(v)}</strong><small>{safe(n)}</small></div>' for i,n,v in cards)
 records=f'<div class="records"><div><span>🏆 Meiste Wünsche</span><strong>{safe(top_req[0])}</strong><small>{top_req[1]} Wünsche</small></div><div><span>🔥 Meiste Upvotes</span><strong>{safe(top_vote["title"]) if top_vote else "–"}</strong><small>{int(top_vote.get("votes") or 0) if top_vote else 0} Votes</small></div><div><span>🎸 Top-Künstler/Kanal</span><strong>{safe(top_artist[0])}</strong><small>{top_artist[1]} Titel</small></div><div><span>🔥 Hype des Abends</span><strong>{safe(top_hype['title']) if top_hype else '–'}</strong><small>{int(top_hype.get('hypes') or 0) if top_hype else 0} Hypes</small></div><div><span>📻 Musikmix</span><strong>{len(requests)} Wünsche / {len(bases)} Basis</strong><small>{len(rows)} Titel insgesamt</small></div></div>'
 tracks=[]
 for i,r in enumerate(rows,1):
  d=local_time(r.get('started_at') or r.get('created_at'));clock=d.strftime('%H:%M') if d else '–';source='Wunsch' if r['source']=='request' else 'Grundplaylist';status='übersprungen' if r['status']=='skipped' else 'gespielt';who=r.get('requested_by') if r['source']=='request' else 'Grundplaylist'
  tracks.append(f'<article class="track"><div class="number">{i}</div><div class="time">{clock}</div><img src="{safe(r.get("thumbnail"))}" alt=""><div><h3>{safe(r["title"])}</h3><p>{safe(r.get("channel"))}</p><div class="meta"><span>👤 {safe(who)}</span><span>👍 {int(r.get("votes") or 0)}</span><span>🎶 {source}</span><span>🔥 {int(r.get('hypes') or 0)}</span><span>{status}</span></div></div><a href="https://www.youtube.com/watch?v={safe(r["video_id"])}" target="_blank" rel="noopener">YouTube ↗</a></article>')
 ranking=''.join(f'<li><span>{safe(n)}</span><strong>{v}</strong></li>' for n,v in sorted(requesters.items(),key=lambda x:(-x[1],x[0]))[:10]) or '<li><span>Keine Wünsche</span><strong>0</strong></li>'
 banner = p.get("banner_path") or ""

hero_style = ""

if banner:
    hero_style = (
        "background-image:"
        "linear-gradient("
        "rgba(0,0,0,.35),"
        "rgba(0,0,0,.55)"
        "),"
        f"url('{safe(banner)}');"
        "background-size:cover;"
        "background-position:center;"
    )
return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe(p['name'])} – Party Recap</title><style>:root{{--card:#141b2d;--line:#283653;--text:#f8fafc;--muted:#9ca9bf;--blue:#38bdf8}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,#18264a,#090d18 38%);color:var(--text);font-family:system-ui}}main{{max-width:980px;margin:auto;padding:32px 18px 70px}}.hero{{text-align:center;padding:42px 22px;background:linear-gradient(135deg,#172554dd,#3b0764cc);border:1px solid #4c5c88;border-radius:28px;background-size:cover;background-position:center}}h1{{font-size:clamp(38px,7vw,72px);margin:8px 0}}.hero p{{line-height:1.65;font-size:19px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}.stat,.records>div,.panel{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px}}.stat strong,.stat small,.records span,.records strong,.records small{{display:block}}.stat strong{{font-size:25px;margin:7px 0}}small,p{{color:var(--muted)}}.records{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.panel{{margin-top:20px}}.track{{display:grid;grid-template-columns:34px 48px 72px 1fr auto;gap:10px;align-items:center;padding:13px 0;border-top:1px solid var(--line)}}.track img{{width:72px;aspect-ratio:16/9;object-fit:cover;border-radius:9px}}.track h3,.track p{{margin:0}}.number,.time,a{{color:var(--blue);font-weight:700}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;font-size:12px}}.meta span{{background:#1f2937;padding:4px 8px;border-radius:99px}}.ranking{{list-style:none;padding:0}}.ranking li{{display:flex;justify-content:space-between;padding:10px;border-top:1px solid var(--line)}}footer{{text-align:center;color:var(--muted);margin-top:34px}}@media(max-width:700px){{.stats{{grid-template-columns:repeat(2,1fr)}}.records{{grid-template-columns:1fr}}.track{{grid-template-columns:30px 42px 1fr}}.track img{{display:none}}.track>a{{grid-column:3}}}}@media print{{body{{background:white;color:#111}}.hero,.stat,.records>div,.panel{{background:white;color:#111}}}}</style></head><body><main><header
  class="hero"
  style="{hero_style}"
><div style="font-size:52px">🎉</div><h1>{safe(p['name'])}</h1><p>Hier ist die Playlist unserer <strong>{safe(p['name'])}</strong> vom <strong>{date_text}</strong>.<br>Losgelegt haben wir um <strong>{start_text}</strong> und <strong>{duration_text(seconds)}</strong> durchgehalten.<br>Danke für den schönen Abend! 🍻🎵</p></header><div class="stats">{cards_html}</div>{records}<section class="panel"><h2>🏅 Wunschgeber-Ranking</h2><ol class="ranking">{ranking}</ol></section><section class="panel"><h2>🎶 Unsere Playlist</h2>{''.join(tracks) if tracks else '<p>Keine gespielten Titel vorhanden.</p>'}</section><footer>Erstellt mit SmartTube PartyQueue · Party Recap V2.7</footer></main></body></html>"""

def recap_pdf(p,rows):
 out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=15*mm,bottomMargin=15*mm,title=f"{p['name']} - Party Recap",author='SmartTube PartyQueue')
 styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='RecapTitle',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=24,leading=29,textColor=colors.HexColor('#172554'),alignment=TA_CENTER,spaceAfter=8));styles.add(ParagraphStyle(name='Intro',parent=styles['BodyText'],fontSize=11,leading=16,alignment=TA_CENTER,spaceAfter=12));styles.add(ParagraphStyle(name='Small',parent=styles['BodyText'],fontSize=8,leading=10));styles.add(ParagraphStyle(name='Song',parent=styles['BodyText'],fontSize=9,leading=11));styles.add(ParagraphStyle(name='Section',parent=styles['Heading2'],fontSize=15,leading=18,textColor=colors.HexColor('#172554'),spaceBefore=10,spaceAfter=7))
 start=next((local_time(r.get('started_at') or r.get('created_at')) for r in rows if local_time(r.get('started_at') or r.get('created_at'))),local_time(p.get('started_at')));end=local_time(p.get('ended_at')) or next((local_time(r.get('finished_at')) for r in reversed(rows) if r.get('finished_at')),None) or datetime.now(ZoneInfo(settings.tz));seconds=max(0,(end-start).total_seconds()) if start else 0
 requests=[r for r in rows if r['source']=='request'];played=[r for r in rows if r['status']=='played'];skipped=[r for r in rows if r['status']=='skipped'];requesters={};artists={}
 for r in requests:
  n=(r.get('requested_by') or 'Gast').strip() or 'Gast';requesters[n]=requesters.get(n,0)+1
 for r in rows:
  n=(r.get('channel') or 'Unbekannt').strip() or 'Unbekannt';artists[n]=artists.get(n,0)+1
 top_req=max(requesters.items(),key=lambda x:(x[1],x[0])) if requesters else ('-',0);top_artist=max(artists.items(),key=lambda x:(x[1],x[0])) if artists else ('-',0);top_vote=max(rows,key=lambda r:(r.get('votes') or 0,r.get('title') or''),default=None);votes=sum(int(r.get('votes') or 0) for r in rows);hypes=sum(int(r.get('hypes') or 0) for r in rows);top_hype=max(rows,key=lambda r:(r.get('hypes') or 0,r.get('title') or''),default=None);date_text=start.strftime('%d.%m.%Y') if start else 'ohne Datum';start_text=start.strftime('%H:%M Uhr') if start else 'unbekannter Uhrzeit'
 story = []

 banner = p.get("banner_path") or ""

 if banner:

   try:

     banner_file = (
       Path(settings.data_dir)
       / banner.replace(
         "/banners/",
         "banners/"
       )
     )

     if banner_file.exists():

       story.append(
         Image(
           str(banner_file),
           width=170 * mm,
           height=55 * mm
         )
       )

       story.append(
         Spacer(
           1,
           4 * mm
         )
       )

   except Exception:
     pass
 story.extend([Paragraph(xml_escape(p['name']),styles['RecapTitle']),Paragraph(f"Hier ist die Playlist unserer <b>{xml_escape(p['name'])}</b> vom <b>{date_text}</b>.<br/>Losgelegt haben wir um <b>{start_text}</b> und <b>{duration_text(seconds)}</b> durchgehalten.<br/>Danke fuer den schoenen Abend!",styles['Intro'])])
 stats=[['Titel gespielt',str(len(played)),'Wuensche',str(len(requests))],['Upvotes',str(votes),'Wunschgeber',str(len(requesters))],['Partydauer',duration_text(seconds),'Hypes',str(hypes)]];t=Table(stats,colWidths=[36*mm,25*mm,36*mm,35*mm],hAlign='CENTER');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#eef2ff')),('TEXTCOLOR',(0,0),(-1,-1),colors.HexColor('#172554')),('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),('BOX',(0,0),(-1,-1),0.8,colors.HexColor('#64748b')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(1,0),(1,-1),'CENTER'),('ALIGN',(3,0),(3,-1),'CENTER'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.extend([t,Spacer(1,5*mm),Paragraph('Rekorde',styles['Section'])])
 record_data=[['Meiste Wuensche',f'{top_req[0]} ({top_req[1]})'],['Meiste Upvotes',f"{top_vote['title']} ({int(top_vote.get('votes') or 0)})" if top_vote else '-'],['Top-Kuenstler/Kanal',f'{top_artist[0]} ({top_artist[1]})'],['Hype des Abends',f"{top_hype['title']} ({int(top_hype.get('hypes') or 0)})" if top_hype else '-']];rt=Table(record_data,colWidths=[48*mm,112*mm]);rt.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#172554')),('TEXTCOLOR',(0,0),(0,-1),colors.white),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.extend([rt,Spacer(1,4*mm),Paragraph('Wunschgeber-Ranking',styles['Section'])])
rank=[['#','Name','Wuensche']]+[[str(i),xml_escape(n),str(v)] for i,(n,v) in enumerate(sorted(requesters.items(),key=lambda x:(-x[1],x[0]))[:10],1)];rankt=Table(rank,colWidths=[12*mm,120*mm,28*mm],repeatRows=1);rankt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#2563eb')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#cbd5e1')),('ALIGN',(0,0),(0,-1),'CENTER'),('ALIGN',(2,0),(2,-1),'CENTER'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([rankt,PageBreak(),Paragraph('Unsere Playlist',styles['Section'])])
tracks=[['#','Zeit','Titel / Kanal','Wunschgeber','Votes']]
for i,r in enumerate(rows,1):
  d=local_time(r.get('started_at') or r.get('created_at'));clock=d.strftime('%H:%M') if d else '-';who=r.get('requested_by') if r['source']=='request' else 'Grundplaylist';status='uebersprungen' if r['status']=='skipped' else 'gespielt';tracks.append([str(i),clock,Paragraph(f"<b>{xml_escape(r['title'])}</b><br/><font color='#64748b'>{xml_escape(r.get('channel') or '')} - {status} - Hype {int(r.get('hypes') or 0)}</font>",styles['Song']),Paragraph(xml_escape(who or ''),styles['Small']),str(int(r.get('votes') or 0))])
tt=Table(tracks,colWidths=[10*mm,16*mm,81*mm,37*mm,16*mm],repeatRows=1);tt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#172554')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),8),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#cbd5e1')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(1,-1),'CENTER'),('ALIGN',(4,0),(4,-1),'CENTER'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')]),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story.append(tt)
def footer(canvas,doc):canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#64748b'));canvas.drawString(16*mm,8*mm,'Erstellt mit SmartTube PartyQueue V2.8.0');canvas.drawRightString(A4[0]-16*mm,8*mm,f'Seite {doc.page}');canvas.restoreState()
doc.build(story,onFirstPage=footer,onLaterPages=footer);out.seek(0);return out

@app.get('/api/party/{pid}/export/{fmt}')
async def export(pid:int,fmt:str,password:str='',x_admin_password:str=Header(default='')):
 au(x_admin_password or password)
 with conn() as c:
  pr=c.execute('SELECT * FROM parties WHERE id=?',(pid,)).fetchone()
  if not pr:raise HTTPException(404,'Party nicht gefunden')
  p=dict(pr);rows=[dict(r) for r in c.execute("SELECT queue.created_at,queue.started_at,queue.finished_at,queue.title,queue.channel,queue.thumbnail,queue.duration_seconds,queue.video_id,queue.source,queue.requested_by,queue.votes,queue.target_tv,queue.status,(SELECT COUNT(*) FROM hype_votes hv WHERE hv.queue_id=queue.id) hypes FROM queue WHERE party_id=? AND status IN ('played','skipped') ORDER BY COALESCE(started_at,created_at),id",(pid,))]
 if fmt=='json':return StreamingResponse(io.BytesIO(json.dumps({'party':p,'tracks':rows},ensure_ascii=False,indent=2).encode()),media_type='application/json')
 if fmt=='csv':
  o=io.StringIO();w=csv.DictWriter(o,fieldnames=rows[0].keys() if rows else ['title']);w.writeheader();w.writerows(rows);return StreamingResponse(io.BytesIO(o.getvalue().encode('utf-8-sig')),media_type='text/csv')
 if fmt=='m3u':return PlainTextResponse('#EXTM3U\n'+''.join(f"#EXTINF:-1,{r['title']}\nhttps://www.youtube.com/watch?v={r['video_id']}\n" for r in rows))
 if fmt=='html':return HTMLResponse(recap_html(p,rows))
 if fmt=='pdf':return StreamingResponse(recap_pdf(p,rows),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename=party-recap-{pid}.pdf'})
 raise HTTPException(400,'Format unbekannt')

