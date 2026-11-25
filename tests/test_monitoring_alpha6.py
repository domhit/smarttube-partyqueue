import asyncio
from unittest.mock import AsyncMock,patch

def test_disabled_tv_stops_without_rest_poll():
 import app.main as m
 m.device_monitoring_state.clear();m.rest_unavailable_since.clear();m.pb['tv']={'state':'playing'}
 tv={'id':'tv','enabled':0}
 with patch.object(m,'party',return_value={'id':1,'allowed_devices':'tv'}),patch.object(m,'rest_state',new=AsyncMock()) as rest:
  asyncio.run(m.poll_rest_tv(tv));rest.assert_not_awaited();assert m.device_monitoring_state['tv']=='disabled';assert 'tv' not in m.rest_unavailable_since

def test_not_allowed_tv_stops_without_rest_poll():
 import app.main as m
 m.device_monitoring_state.clear();m.rest_unavailable_since.clear()
 tv={'id':'tv','enabled':1}
 with patch.object(m,'party',return_value={'id':1,'allowed_devices':'other'}),patch.object(m,'rest_state',new=AsyncMock()) as rest:
  asyncio.run(m.poll_rest_tv(tv));rest.assert_not_awaited();assert m.device_monitoring_state['tv']=='not_allowed'

def test_prefetch_does_not_repeat_unchanged_event():
 import app.main as m
 m.play_pending.clear();m.sync_recovery.clear();m.guard.clear();m.queue_recovery_after.clear();m.rest_unavailable_since.clear();m.natural_end_pending.clear();m.queue_prefetch_locks.clear();m.queue_prefetch_state.clear()
 p={'id':1,'sync_mode':0,'default_tv':'tv','allowed_devices':'tv'};tv={'id':'tv','enabled':1};cands=[{'id':2,'video_id':'B'},{'id':3,'video_id':'C'}];q={'currentIndex':0,'currentVideoId':'A','items':[{'videoId':'A'},{'videoId':'B'},{'videoId':'C'}]}
 with patch.object(m,'party',return_value=p),patch.object(m,'get_tv',return_value=tv),patch.object(m,'ensure_queue_candidates',return_value=cands),patch.object(m,'rest_queue_state',new=AsyncMock(return_value=q)),patch.object(m,'debug_event') as dbg:
  asyncio.run(m.prefetch_next('tv','tv'));first=len([x for x in dbg.call_args_list if x.args and x.args[0]=='QUEUE_PREFETCHED']);asyncio.run(m.prefetch_next('tv','tv'));second=len([x for x in dbg.call_args_list if x.args and x.args[0]=='QUEUE_PREFETCHED']);assert first==2 and second==2
