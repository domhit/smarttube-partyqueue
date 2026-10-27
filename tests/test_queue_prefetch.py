import asyncio
from unittest.mock import patch

def test_prefetch_builds_current_next_reserve():
 import app.main as main
 main.play_pending.clear();main.guard.clear();main.queue_prefetch_locks.clear();main.sync_mismatch_after.clear();main.diag.clear();queue={'currentIndex':0,'currentVideoId':'A','items':[{'index':0,'videoId':'A'}]};candidates=[{'id':2,'video_id':'B'},{'id':3,'video_id':'C'}]
 async def state(_):return {'currentIndex':0,'currentVideoId':'A','items':[dict(x) for x in queue['items']]}
 async def add(_,v):queue['items'].append({'index':len(queue['items']),'videoId':v})
 async def move(_,a,b):item=queue['items'].pop(a);queue['items'].insert(b,item);[x.update(index=i) for i,x in enumerate(queue['items'])]
 async def remove(_,v):queue['items'][:]=[x for x in queue['items'] if x['videoId']!=v]
 async def sleep(_):pass
 with patch.object(main,'ensure_queue_candidates',return_value=candidates),patch.object(main,'get_tv',return_value={'id':'tv'}),patch.object(main,'rest_queue_state',new=state),patch.object(main,'rest_queue_add',new=add),patch.object(main,'rest_queue_move',new=move),patch.object(main,'rest_queue_remove',new=remove),patch.object(main.asyncio,'sleep',new=sleep):assert asyncio.run(main.prefetch_next('tv','tv')) is True
 assert [x['videoId'] for x in queue['items']]==['A','B','C']
