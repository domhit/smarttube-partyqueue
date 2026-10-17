from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    tz: str = 'Europe/Berlin'
    youtube_api_key: str = ''
    ha_url: str = 'http://homeassistant.local:8123'
    ha_webhook_id: str = 'smarttube_partyqueue_play'
    ha_token: str = ''
    admin_password: str = 'change-me'
    public_base_url: str = 'http://partyqueue.local:8787'
    max_video_minutes: int = 12
    max_requests_per_guest: int = 3
    search_cache_hours: int = 24
    search_min_length: int = 3
    search_results: int = 10
    smarttube_package: str = 'com.teamsmart.videomanager.tv'
    tv_entity: str = 'media_player.tv_game_adb'

settings = Settings()
