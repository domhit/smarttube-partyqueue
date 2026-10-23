import asyncio,time
from unittest.mock import AsyncMock,patch

def test_rest_sync_seek_after_two_confirmed_samples():
 import app.main as main
 now=time.monotonic();p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'}
 main.pb.clear();main.sync_drift_samples.clear();main.sync_seek_after.clear();main.sync_mismatch_after.clear()
 main.pb.update({'lead':{'state':'playing','media_position':10,'video_id':'same','received':now},'follower':{'state':'playing','media_position':13,'video_id':'same','received':now}})
 with patch.object(main,'party',return_value=p),patch.object(main,'pub',return_value={'allowed_devices':[{'id':'lead'},{'id':'follower'}]}),patch.object(main,'rest_media_command',new=AsyncMock(return_value=True)) as c:
  asyncio.run(main.sync_followers());asyncio.run(main.sync_followers())
  assert any(x.args[:2]==('follower','seek') for x in c.await_args_list)

def test_video_mismatch_switches_video_without_seek():
 import app.main as main
 now=time.monotonic();p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'}
 main.pb.clear();main.sync_mismatch_after.clear()
 main.pb.update({'lead':{'state':'playing','media_position':10,'video_id':'lead-video','received':now},'follower':{'state':'playing','media_position':99,'video_id':'old-video','received':now}})
 with patch.object(main,'party',return_value=p),patch.object(main,'pub',return_value={'allowed_devices':[{'id':'lead'},{'id':'follower'}]}),patch.object(main,'get_tv',return_value={'id':'follower'}),patch.object(main,'rest_play',new=AsyncMock(return_value=True)) as play,patch.object(main,'rest_media_command',new=AsyncMock(return_value=True)) as command:
  asyncio.run(main.sync_followers());play.assert_awaited_once();command.assert_not_awaited()
