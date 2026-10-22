import asyncio
from unittest.mock import AsyncMock, patch

def test_rest_sync_seek():
 import app.main as main
 p={'id':1,'sync_mode':1,'default_tv':'lead','allowed_devices':'lead,follower'}
 main.pb.clear();main.sync_last_state.clear()
 main.pb.update({'lead':{'state':'playing','media_position':10},'follower':{'state':'playing','media_position':13}})
 with patch.object(main,'party',return_value=p),patch.object(main,'pub',return_value={'allowed_devices':[{'id':'lead'},{'id':'follower'}]}),patch.object(main,'rest_media_command',new=AsyncMock(return_value=True)) as cmd:
  asyncio.run(main.sync_followers())
  assert any(c.args[:2]==('follower','seek') for c in cmd.await_args_list)
