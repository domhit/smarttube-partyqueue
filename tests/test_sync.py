import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch


def test_sync_schema_and_settings():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict('os.environ', {'DATA_DIR': tmp, 'ADMIN_PASSWORD': 'test'}):
            import app.db as db
            db.DB = Path(tmp) / 'partyqueue.db'
            db.init_db()
            with db.conn() as c:
                columns = {row['name'] for row in c.execute('PRAGMA table_info(parties)')}
                settings = {row['key'] for row in c.execute("SELECT key FROM settings_store WHERE key LIKE 'sync_%'")}
            assert 'sync_mode' in columns
            assert settings == {'sync_drift_tolerance', 'sync_resume_margin'}


def test_ahead_follower_is_paused():
    import app.main as main
    party = {'id': 1, 'sync_mode': 1, 'default_tv': 'lead', 'allowed_devices': 'lead,follower'}
    main.pb.clear(); main.sync_hold.clear(); main.sync_last_state.clear()
    main.pb.update({'lead': {'state': 'playing', 'media_position': 10}, 'follower': {'state': 'playing', 'media_position': 13}})
    devices = [{'id': 'lead'}, {'id': 'follower'}]
    with patch.object(main, 'party', return_value=party), patch.object(main, 'pub', return_value={'allowed_devices': devices}), patch.object(main, 'adb_media_key', new=AsyncMock(return_value=True)) as key:
        asyncio.run(main.sync_followers())
        assert main.sync_hold['follower'] is True
        assert any(call.args[:2] == ('follower', 127) for call in key.await_args_list)
