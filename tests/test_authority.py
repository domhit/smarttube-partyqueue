import asyncio,time
from unittest.mock import AsyncMock,patch

def test_foreign_video_is_rejected_and_expected_restarted():
 import app.main as main
 expected={'id':7,'video_id':'A','target_tv':'lead'}
 with patch.object(main,'playing_item',return_value=expected),patch.object(main,'send_play_command_to_tv',new=AsyncMock(return_value=True)) as send,patch.object(main,'arm_start_guard'),patch.object(main,'prefetch_party_queue',new=AsyncMock()),patch.object(main,'cast',new=AsyncMock()):
  assert asyncio.run(main.enforce_partyqueue_video('lead',{'id':1},'X')) is True
  send.assert_awaited_once_with(expected,'lead',1)

def test_desired_window_uses_lead_queue_only():
 import app.main as main
 p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'}
 with patch.object(main,'playing_item',return_value={'video_id':'A'}),patch.object(main,'ensure_queue_candidates',return_value=[{'video_id':'B'},{'video_id':'C'}]) as candidates:
  current,future=main.desired_queue_window(p)
  candidates.assert_called_once_with('lead',2);assert current['video_id']=='A';assert [x['video_id'] for x in future]==['B','C']

def test_follower_missing_anchor_triggers_queue_reset():
 import app.main as main
 p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'};main.play_pending.clear();main.guard.clear();main.queue_prefetch_locks.clear()
 with patch.object(main,'party',return_value=p),patch.object(main,'desired_queue_window',return_value=({'id':1,'video_id':'A'},[{'id':2,'video_id':'B'},{'id':3,'video_id':'C'}])),patch.object(main,'get_tv',return_value={'id':'follower'}),patch.object(main,'rest_queue_state',new=AsyncMock(return_value={'currentIndex':-1,'currentVideoId':'','items':[]})),patch.object(main,'reset_device_queue',new=AsyncMock(return_value=True)) as reset:
  assert asyncio.run(main.prefetch_next('follower','lead')) is True
  reset.assert_awaited_once()

def test_identical_multisync_queue_needs_no_mutation():
 import app.main as main
 p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'};main.play_pending.clear();main.guard.clear();main.queue_prefetch_locks.clear()
 q={'currentIndex':0,'currentVideoId':'A','items':[{'index':0,'videoId':'A'},{'index':1,'videoId':'B'},{'index':2,'videoId':'C'}]}
 with patch.object(main,'party',return_value=p),patch.object(main,'desired_queue_window',return_value=({'id':1,'video_id':'A'},[{'id':2,'video_id':'B'},{'id':3,'video_id':'C'}])),patch.object(main,'get_tv',return_value={'id':'follower'}),patch.object(main,'rest_queue_state',new=AsyncMock(return_value=q)),patch.object(main,'rest_queue_add',new=AsyncMock()) as add,patch.object(main,'rest_queue_move',new=AsyncMock()) as move:
  assert asyncio.run(main.prefetch_next('follower','lead')) is True;add.assert_not_awaited();move.assert_not_awaited()
