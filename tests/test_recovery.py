import asyncio,time
from unittest.mock import AsyncMock,patch

def test_watchdog_runs_foreground_recovery_for_idle_player():
 import app.main as main
 main.play_pending.clear();main.play_pending['tv']={'queue_id':1,'video_id':'video','requested':time.monotonic(),'task':None}
 x={'id':1,'video_id':'video','title':'Titel','target_tv':'tv'}
 idle={'videoId':'','isPlaying':False,'isLoading':False};playing={'videoId':'video','isPlaying':True,'isLoading':False}
 async def no_sleep(_):return None
 with patch.object(main.asyncio,'sleep',new=no_sleep),patch.object(main,'send_play_command',new=AsyncMock(return_value=True)),patch.object(main,'get_tv',return_value={'id':'tv'}),patch.object(main,'rest_state',new=AsyncMock(side_effect=[idle,playing])),patch.object(main,'bootstrap_smarttube_with_video',new=AsyncMock(return_value=True)) as recover,patch.object(main,'arm_start_guard'),patch.object(main,'cast',new=AsyncMock()),patch.object(main,'prefetch_party_queue',new=AsyncMock()):
  asyncio.run(main.play_watchdog('tv',1,x));recover.assert_awaited_once();assert 'tv' not in main.play_pending

def test_idle_progress_does_not_finish_pending_track():
 import app.main as main
 p={'id':1,'sync_mode':0,'default_tv':'tv','allowed_devices':'tv'};main.play_pending.clear();main.pb.clear();main.guard.clear();main.play_pending['tv']={'queue_id':1,'video_id':'video','requested':time.monotonic(),'task':None}
 progress=main.Progress(target_tv='tv',state='idle',media_position=0,app_id='smarttube_rest',video_id='')
 class Row(dict):
  def __getattr__(self,k):return self[k]
 class Cursor:
  def execute(self,*a,**k):return self
  def fetchone(self):return Row(id=1,video_id='video',duration_seconds=100,title='Titel')
 class Ctx:
  def __enter__(self):return Cursor()
  def __exit__(self,*a):pass
 with patch.object(main,'party',return_value=p),patch.object(main,'tvok',return_value='tv'),patch.object(main,'conn',return_value=Ctx()),patch.object(main,'done',new=AsyncMock()) as done,patch.object(main,'cast',new=AsyncMock()):
  result=asyncio.run(main.process_progress(progress));assert result.get('play_pending') is True;done.assert_not_awaited()
