from unittest.mock import patch
import asyncio

def test_prefetch_pauses_during_natural_end_transition():
 import app.main as m
 m.play_pending.clear();m.sync_recovery.clear();m.guard.clear();m.queue_recovery_after.clear();m.rest_unavailable_since.clear();m.natural_end_pending.clear()
 m.natural_end_pending['tv']={'queue_id':1,'video_id':'A','detected_at':0}
 with patch.object(m,'ensure_queue_candidates') as candidates:
  assert asyncio.run(m.prefetch_next('tv','tv')) is False
  candidates.assert_not_called()
 m.natural_end_pending.clear()
