import asyncio
from unittest.mock import AsyncMock,patch

def test_current_video_is_not_readded_and_existing_next_is_kept():
 import app.main as m
 m.play_pending.clear();m.sync_recovery.clear();m.guard.clear();m.queue_recovery_after.clear();m.rest_unavailable_since.clear();m.queue_prefetch_locks.clear()
 candidates=[{'id':2,'video_id':'B'},{'id':3,'video_id':'C'}]
 states=[{'currentIndex':0,'currentVideoId':'A','items':[{'index':0,'videoId':'A'},{'index':99,'videoId':'B'},{'index':100,'videoId':'C'}]}]*5
 with patch.object(m,'ensure_queue_candidates',return_value=candidates),patch.object(m,'get_tv',return_value={'id':'tv'}),patch.object(m,'rest_queue_state',new=AsyncMock(side_effect=states)),patch.object(m,'rest_queue_add',new=AsyncMock()) as add,patch.object(m,'rest_queue_remove',new=AsyncMock()) as remove,patch.object(m,'rest_queue_move',new=AsyncMock()) as move:
  assert asyncio.run(m.prefetch_next('tv','tv')) is True
  add.assert_not_awaited();remove.assert_not_awaited();move.assert_not_awaited()

def test_queue_add_waits_until_item_becomes_visible():
 import app.main as m
 m.play_pending.clear();m.sync_recovery.clear();m.guard.clear();m.queue_recovery_after.clear();m.rest_unavailable_since.clear();m.queue_prefetch_locks.clear()
 candidates=[{'id':2,'video_id':'B'}]
 missing={'currentIndex':0,'currentVideoId':'A','items':[{'index':0,'videoId':'A'}]};visible={'currentIndex':0,'currentVideoId':'A','items':[{'index':0,'videoId':'A'},{'index':1,'videoId':'B'}]}
 async def no_sleep(_):pass
 with patch.object(m,'ensure_queue_candidates',return_value=candidates),patch.object(m,'get_tv',return_value={'id':'tv'}),patch.object(m,'rest_queue_state',new=AsyncMock(side_effect=[missing,missing,visible,visible])),patch.object(m,'rest_queue_add',new=AsyncMock()) as add,patch.object(m.asyncio,'sleep',new=no_sleep):
  assert asyncio.run(m.prefetch_next('tv','tv')) is True
  add.assert_awaited_once_with({'id':'tv'},'B')

def test_prefetch_pauses_during_natural_end_transition():
 import app.main as m
 m.play_pending.clear();m.sync_recovery.clear();m.guard.clear();m.queue_recovery_after.clear();m.rest_unavailable_since.clear();m.natural_end_pending.clear()
 m.natural_end_pending['tv']={'queue_id':1,'video_id':'A','detected_at':0}
 with patch.object(m,'ensure_queue_candidates') as candidates:
  assert asyncio.run(m.prefetch_next('tv','tv')) is False
  candidates.assert_not_called()
 m.natural_end_pending.clear()
