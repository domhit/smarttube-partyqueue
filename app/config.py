from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
 tz:str='Europe/Berlin';youtube_api_key:str='';ha_url:str='http://homeassistant.local:8123';ha_webhook_id:str='smarttube_partyqueue_play';admin_password:str='change-me';data_dir:str='/app/data';max_video_minutes:int=12;max_requests_per_guest:int=3;search_cache_hours:int=168;search_min_length:int=3;search_results:int=50;youtube_search_daily_limit:int=100;youtube_search_warning_at:int=80;youtube_search_hard_stop_at:int=98;base_playlist_recent_exclude:int=20;prestart_seconds:float=4;idle_fallback_delay:float=2;prestart_idle_guard:float=10;external_skip_min_previous:float=30;external_skip_max_new:float=8;play_confirm_timeout:float=6;play_retry_timeout:float=10;play_webhook_timeout:float=5;play_confirm_max_position:float=20;adb_poll_interval:float=2;smarttube_package:str='org.smarttube.stable'

settings=Settings()
