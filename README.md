# SmartTube PartyQueue V4

REST-only Entwicklung für den Branch `develop-v4`. PartyQueue kommuniziert ausschließlich mit der SmartTube REST API.

## Voraussetzungen
- SmartTube-REST-Fork auf jedem Zielgerät
- REST API aktiviert, Standardport 8090
- Benutzer und Passwort je TV

## Start
```bash
cp .env.example .env
docker compose up -d --build
```
Danach unter **Host → TVs** Host, Port, Benutzer und Passwort eintragen und die API testen.

## V4
- Wiedergabestart über `/api/v1/play`
- Telemetrie über `/api/v1/playbackstate`
- Multi-TV Play/Pause/Seek über REST
- kein ADB und kein Home Assistant
