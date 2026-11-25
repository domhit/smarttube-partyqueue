import asyncio,time
from unittest.mock import AsyncMock,patch

def test_foreign_video_is_rejected():
 import app.main as main
 expected={'id':7,'video_id':'A','target_tv':'lead'}
 with patch.object(main,'playing_item',return_value=expected),patch.object(main,'send_play_command_to_tv',new=AsyncMock(return_value=True)) as send,patch.object(main,'arm_start_guard'),patch.object(main,'prefetch_party_queue',new=AsyncMock()),patch.object(main,'cast',new=AsyncMock()):
  assert asyncio.run(main.enforce_partyqueue_video('lead',{'id':1},'X')) is True;send.assert_awaited_once_with(expected,'lead',1)

def test_recovery_cooldown_blocks_prefetch():
 import app.main as main
 main.queue_recovery_after['tv']=time.monotonic()+10;main.play_pending.clear();main.guard.clear()
 with patch.object(main,'party',return_value={'id':1,'sync_mode':0,'default_tv':'tv','allowed_devices':'tv'}):assert asyncio.run(main.prefetch_next('tv','tv')) is False
