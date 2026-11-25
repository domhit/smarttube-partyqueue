import sqlite3
from app.main import select_queue_candidates

def db():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE queue(id INTEGER PRIMARY KEY, party_id INTEGER, target_tv TEXT, status TEXT, video_id TEXT, title TEXT, source TEXT, admin_priority INTEGER, votes INTEGER, position INTEGER)')
 return c

def add(c,id,source,position,votes=0,admin=0,video=None):
 c.execute('INSERT INTO queue VALUES(?,?,?,?,?,?,?,?,?,?)',(id,1,'tv','queued',video or str(id),str(id),source,admin,votes,position))

def party(upvote=1):return {'id':1,'upvote_sort':upvote}

def test_request_beats_older_base_fallback():
 c=db();add(c,1,'base',0);add(c,2,'request',1)
 assert select_queue_candidates(c,party(),'tv',2)[0]['id']==2

def test_prefetch_and_next_can_share_exact_order():
 c=db();add(c,1,'base',0);add(c,2,'request',2);add(c,3,'request',1)
 ids=[x['id'] for x in select_queue_candidates(c,party(),'tv',3)]
 assert ids==[3,2,1]

def test_votes_order_requests_when_enabled():
 c=db();add(c,1,'request',1,votes=1);add(c,2,'request',2,votes=5)
 assert select_queue_candidates(c,party(1),'tv',2)[0]['id']==2

def test_admin_priority_is_explicit_override():
 c=db();add(c,1,'base',0,admin=10);add(c,2,'request',1)
 assert select_queue_candidates(c,party(),'tv',2)[0]['id']==1

def test_current_video_can_be_excluded():
 c=db();add(c,1,'request',1,video='A');add(c,2,'request',2,video='B')
 assert [x['video_id'] for x in select_queue_candidates(c,party(),'tv',2,'A')]==['B']
