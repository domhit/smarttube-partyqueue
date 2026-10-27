import asyncio
from unittest.mock import AsyncMock,patch

def test_prefetch_builds_current_next_reserve():
 import app.main as main
 main.play_pending.clear();main.guard.clear();main.queue_prefetch_locks.clear();main.sync_mismatch_after.clear();main.diag.clear()
 queue={'currentIndex':0,'currentVideoId':'A','items':[{'index':0,'videoId':'A'}]}
 candidates=[{'id':2,'video_id':'B'},{'id':3,'video_id':'C'}]
 async def queue_state(_):return {'currentIndex':queue['currentIndex'],'currentVideoId':queue['currentVideoId'],'items':[dict(x) for x in queue['items']]}
 async def queue_add(_,video_id):queue['items'].append({'index':len(queue['items']),'videoId':video_id});return {}
 async def queue_move(_,source,target):
  item=queue['items'].pop(source);queue['items'].insert(target,item)
  for index,row in enumerate(queue['items']):row['index']=index
  return {}
 async def queue_remove(_,video_id):
  queue['items']=[x for x in queue['items'] if x['videoId']!=video_id]
  for index,row in enumerate(queue['items']):row['index']=index
  return {}
 async def no_sleep(_):return None
 with patch.object(main,'ensure_queue_candidates',return_value=candidates),patch.object(main,'get_tv',return_value={'id':'tv'}),patch.object(main,'rest_queue_state',new=queue_state),patch.object(main,'rest_queue_add',new=queue_add),patch.object(main,'rest_queue_move',new=queue_move),patch.object(main,'rest_queue_remove',new=queue_remove),patch.object(main.asyncio,'sleep',new=no_sleep):
  assert asyncio.run(main.prefetch_next('tv','tv')) is True
 assert [x['videoId'] for x in queue['items']]==['A','B','C']
