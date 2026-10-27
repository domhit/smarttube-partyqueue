import asyncio,time
from unittest.mock import AsyncMock,patch

def test_known_live_track_is_adopted_after_three_samples():
 import app.main as main
 main.live_mismatch.clear();main.unmanaged_live.clear();p={'id':1};current={'id':10};queued={'id':11,'title':'Known'}
 class Cursor:
  calls=0
  def execute(self,*a):self.calls+=1;return self
  def fetchone(self):return current if self.calls==1 else queued
 class Ctx:
  def __enter__(self):return Cursor()
  def __exit__(self,*a):pass
 with patch.object(main,'conn',return_value=Ctx()),patch.object(main,'cast',new=AsyncMock()),patch.object(main,'prefetch_party_queue',new=AsyncMock()):
  assert asyncio.run(main.reconcile_live_state('tv',p,'B','Known',100)) is False
  assert asyncio.run(main.reconcile_live_state('tv',p,'B','Known',100)) is False
  assert asyncio.run(main.reconcile_live_state('tv',p,'B','Known',100)) is True
  assert 'tv' not in main.unmanaged_live

def test_unknown_live_track_is_allowed_to_finish():
 import app.main as main
 main.live_mismatch.clear();main.unmanaged_live.clear();p={'id':1};current={'id':10}
 class Cursor:
  calls=0
  def execute(self,*a):self.calls+=1;return self
  def fetchone(self):return current if self.calls==1 else None
 class Ctx:
  def __enter__(self):return Cursor()
  def __exit__(self,*a):pass
 with patch.object(main,'conn',return_value=Ctx()),patch.object(main,'cast',new=AsyncMock()):
  asyncio.run(main.reconcile_live_state('tv',p,'X','External',90));asyncio.run(main.reconcile_live_state('tv',p,'X','External',90));assert asyncio.run(main.reconcile_live_state('tv',p,'X','External',90)) is True
 assert main.unmanaged_live['tv']['video_id']=='X'

def test_unknown_finish_returns_control_to_partyqueue():
 import app.main as main
 main.unmanaged_live['tv']={'video_id':'X','title':'External','duration':90,'started':time.monotonic()}
 with patch.object(main,'arm_start_guard'),patch.object(main,'cast',new=AsyncMock()),patch.object(main,'nxt',new=AsyncMock(return_value=True)) as nxt:
  assert asyncio.run(main.finish_unmanaged_live('tv',{'id':1},'video_changed','Y')) is True;nxt.assert_awaited_once_with('tv')
