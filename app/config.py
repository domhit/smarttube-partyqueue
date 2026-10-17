from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    tz: str = 'Europe/Berlin'
    youtube_api_key: str = ''
    ha_url: str = 'http://homeassistant.local:8123'
    ha_webhook_id: str = 'smarttube_partyqueue_play'
    admin_password: str = 'change-me'
    public_base_url: str = 'http://partyqueue.local:8787'
    max_video_minutes: int = 12
    max_requests_per_guest: int = 3
    search_cache_hours: int = 24
    search_min_length: int = 3
    search_results: int = 10
    smarttube_package: str = 'org.smarttube.stable'
    default_tv: str = 'ke75'
    tv_devices: str = 'ke75|KE75 Medienzimmer,kd70|KD70 Schlafzimmer'

    def parsed_devices(self) -> list[dict[str, str]]:
        devices = []
        for entry in self.tv_devices.split(','):
            entry = entry.strip()
            if not entry:
                continue
            parts = [part.strip() for part in entry.split('|', 1)]
            device_id = parts[0]
            name = parts[1] if len(parts) > 1 and parts[1] else device_id
            devices.append({'id': device_id, 'name': name})
        if not devices:
            devices = [{'id': self.default_tv, 'name': self.default_tv}]
        if self.default_tv not in {d['id'] for d in devices}:
            self.default_tv = devices[0]['id']
        return devices

settings = Settings()
