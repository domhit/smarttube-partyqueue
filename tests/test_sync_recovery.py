import asyncio,time
from unittest.mock import AsyncMock,patch

def setup(main,follower_state='playing',follower_video='old'):
 now=time.monotonic();main.pb.clear();main.sync_recovery.clear();main.sync_seek_after.clear();main.sync_drift_samples.clear();main.queue_recovery_after.clear();main.pb.update({'lead':{'state':'playing','media_position':20,'video_id':'A','received':now},'follower':{'state':follower_state,'media_position':2,'video_id':follower_video,'received':now}});return {'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'}

def test_mismatch_enters_recovery_and_pauses_prefetch():
 import app.main as main;p=setup(main)
 with patch.object(main,'party',return_value=p),patch.object(main,'pub',return_value={'allowed_devices':[{'id':'lead'},{'id':'follower'}]}),patch.object(main,'get_tv',return_value={'id':'follower'}),patch.object(main,'rest_play',new=AsyncMock(return_value=True)) as play:
  asyncio.run(main.sync_followers());play.assert_awaited_once();assert main.sync_recovery['follower']['video_id']=='A';assert main.queue_recovery_after['follower']>time.monotonic()

def test_two_video_confirmations_do_one_initial_seek():
 import app.main as main;p=setup(main,follower_video='A');main.sync_recovery['follower']={'video_id':'A','confirmed':0,'retry_after':0}
 with patch.object(main,'party',return_value=p),patch.object(main,'pub',return_value={'allowed_devices':[{'id':'lead'},{'id':'follower'}]}),patch.object(main,'rest_media_command',new=AsyncMock(return_value=True)) as command,patch.object(main,'prefetch_next',new=AsyncMock(return_value=True)):
  asyncio.run(main.sync_followers());command.assert_not_awaited();asyncio.run(main.sync_followers());assert [c.args[1] for c in command.await_args_list]==['seek'];assert 'follower' not in main.sync_recovery

def test_no_play_when_both_already_playing():
 import app.main as main;p=setup(main,follower_video='A')
 with patch.object(main,'party',return_value=p),patch.object(main,'pub',return_value={'allowed_devices':[{'id':'lead'},{'id':'follower'}]}),patch.object(main,'rest_media_command',new=AsyncMock(return_value=True)) as command:
  asyncio.run(main.sync_followers());assert not any(c.args[1]=='play' for c in command.await_args_list)
