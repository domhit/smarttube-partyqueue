from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    tz: str = 'Europe/Berlin'
    youtube_api_key: str = ''
    ha_url: str = 'http://homeassistant.local:8123'
    ha_webhook_id: str = 'smarttube_partyqueue_play'
    admin_password: str = 'change-me'
    public_base_url: str = 'http://partyqueue.local:8787'
    data_dir: str = '/app/data'
    max_video_minutes: int = 12
    max_requests_per_guest: int = 3
    search_cache_hours: int = 168
    search_min_length: int = 3
    search_results: int = 50
    youtube_search_daily_limit: int = 100
    youtube_search_warning_at: int = 80
    youtube_search_hard_stop_at: int = 98
    base_playlist_recent_exclude: int = 20
    smarttube_package: str = 'org.smarttube.stable'
    default_tv: str = 'ke75'
    tv_devices: str = 'xi4k|Xiaomi Gästezimmer,ke75|KE75 Spielzimmer,kd70|KD70 Schlafzimmer,fiwo|FireTV Wohnzimmer,fi4k|FireTV Partykeller'

    def parsed_devices(self):
        result = []
        for raw in self.tv_devices.split(','):
            parts = [x.strip() for x in raw.split('|', 1)]
            if parts[0]:
                result.append({'id': parts[0], 'name': parts[1] if len(parts) > 1 else parts[0]})
        return result or [{'id': self.default_tv, 'name': self.default_tv}]

settings = Settings()
