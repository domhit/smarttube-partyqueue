import asyncio,time
from unittest.mock import AsyncMock,patch
from app.main import SmartTubeEvent

def ev(kind,vid='A',seq=1,session='s1'):return SmartTubeEvent(event=kind,session_id=session,sequence=seq,device={'id':'lead'},video={'video_id':vid,'title':'T'},playback={'position_ms':1000,'duration_ms':100000})

def reset(main):main.smarttube_event_sequence.clear();main.smarttube_event_seen.clear();main.pb.clear()

def test_video_ended_marks_played():
 import app.main as m;reset(m);p={'id':1,'sync_mode':0,'default_tv':'lead','allowed_devices':'lead'}
 with patch.object(m,'party',return_value=p),patch.object(m,'playing_item',return_value={'id':1,'video_id':'A'}),patch.object(m,'done',new=AsyncMock()) as done:asyncio.run(m.process_smarttube_event(ev('video_ended'),'lead'));done.assert_awaited_once_with('lead','played','smarttube_video_ended')

def test_user_skip_marks_skipped():
 import app.main as m;reset(m);p={'id':1,'sync_mode':0,'default_tv':'lead','allowed_devices':'lead'}
 with patch.object(m,'party',return_value=p),patch.object(m,'playing_item',return_value={'id':1,'video_id':'A'}),patch.object(m,'done',new=AsyncMock()) as done:asyncio.run(m.process_smarttube_event(ev('user_skip'),'lead'));done.assert_awaited_once_with('lead','skipped','smarttube_user_skip')

def test_sponsorblock_does_not_finish_track():
 import app.main as m;reset(m);p={'id':1,'sync_mode':0,'default_tv':'lead','allowed_devices':'lead'}
 with patch.object(m,'party',return_value=p),patch.object(m,'done',new=AsyncMock()) as done:asyncio.run(m.process_smarttube_event(ev('sponsorblock_skip'),'lead'));done.assert_not_awaited()

def test_follower_event_never_finishes_queue():
 import app.main as m;reset(m);p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'};e=ev('user_skip');e.device={'id':'follower'}
 with patch.object(m,'party',return_value=p),patch.object(m,'done',new=AsyncMock()) as done,patch.object(m,'cast',new=AsyncMock()):asyncio.run(m.process_smarttube_event(e,'follower'));done.assert_not_awaited()

def test_duplicate_sequence_is_ignored():
 import app.main as m;reset(m);p={'id':1,'sync_mode':0,'default_tv':'lead','allowed_devices':'lead'};m.smarttube_event_sequence['lead']={'session_id':'s1','sequence':5}
 with patch.object(m,'party',return_value=p),patch.object(m,'done',new=AsyncMock()) as done:r=asyncio.run(m.process_smarttube_event(ev('video_ended',seq=5),'lead'));assert r['ignored'];done.assert_not_awaited()

def test_new_session_resets_sequence():
 import app.main as m;reset(m);m.smarttube_event_sequence['lead']={'session_id':'old','sequence':99};p={'id':1,'sync_mode':0,'default_tv':'lead','allowed_devices':'lead'}
 with patch.object(m,'party',return_value=p),patch.object(m,'playing_item',return_value={'id':1,'video_id':'A'}),patch.object(m,'done',new=AsyncMock()) as done:r=asyncio.run(m.process_smarttube_event(ev('video_ended',seq=1,session='new'),'lead'));assert not r.get('ignored');done.assert_awaited_once()
