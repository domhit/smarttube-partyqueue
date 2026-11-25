from app.main import classify_tv_health

def test_short_outage_is_yellow():assert classify_tv_health(True,4,1,'A','A','playing',3)['level']=='yellow'
def test_long_outage_is_red():assert classify_tv_health(True,16,1,'A','A','playing',3)['level']=='red'
def test_matching_player_is_green():assert classify_tv_health(True,None,1,'A','A','playing',3)['level']=='green'
def test_mismatch_is_yellow():assert classify_tv_health(True,None,1,'A','B','playing',3)['label']=='Titel abweichend'
def test_disabled_is_gray():assert classify_tv_health(False,None,None,'','','idle',None)['level']=='off'
