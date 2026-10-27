from app.main import classify_tv_health

def test_health_offline_is_red():
 assert classify_tv_health(True,False,'','','offline',0)['level']=='red'

def test_health_idle_without_active_party_is_green():
 assert classify_tv_health(True,True,'','','idle',0)['level']=='green'

def test_health_expected_video_missing_is_yellow():
 assert classify_tv_health(True,True,'abc','','idle',0)['label']=='Player idle'

def test_health_matching_player_and_queue_is_green():
 assert classify_tv_health(True,True,'abc','abc','playing',3)['level']=='green'

def test_health_incomplete_active_queue_is_yellow():
 assert classify_tv_health(True,True,'abc','abc','playing',1)['label']=='Queue unvollständig'

def test_health_mismatched_video_is_yellow():
 assert classify_tv_health(True,True,'abc','def','playing',3)['label']=='Titel abweichend'
