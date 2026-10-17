# SmartTube PartyQueue V2

Selbst gehostete Party-Jukebox für YouTube-Suche, gemeinsame Queue und Wiedergabe in SmartTube via Home Assistant/ADB.

## Enthalten

- YouTube-Suche mit Cache, Thumbnail, Kanal und Dauer
- Linkeingabe und Tampermonkey-Userscript
- Gastlimit, Duplikatschutz, Livestream- und Längenfilter
- Hostansicht mit Sortierung, Löschen, Skip, Sperre und Verlauf
- SQLite-Persistenz und WebSocket-Liveupdates
- Docker Compose
- Home-Assistant-Webhook zum Starten in SmartTube
- Endpoint zur Meldung des Videoendes

## Start

```bash
cp .env.example .env
nano .env
docker compose up -d --build
```

Danach Gastansicht unter `http://SERVER-IP:8787`, Hostansicht unter `http://SERVER-IP:8787/host`.

## YouTube API

In Google Cloud ein Projekt anlegen, **YouTube Data API v3** aktivieren und einen API-Key in `.env` als `YOUTUBE_API_KEY` setzen. Den Key möglichst auf die YouTube Data API beschränken.

## Home Assistant

1. `home-assistant/automation.yaml` übernehmen.
2. `media_player.tv_game_adb` bei Bedarf ersetzen.
3. SmartTube-Paket prüfen: `pm list packages | grep -i smart`.
4. `HA_WEBHOOK_ID` und `webhook_id` müssen identisch sein.
5. Für den automatischen nächsten Titel `video-ended-example.yaml` an deine MediaSession-Entität anpassen.

## Wichtiger Architekturpunkt

SmartTube verwaltet nicht die Queue. Jedes Video wird einzeln per ADB-Intent gestartet. Erst wenn Home Assistant `/api/playback/end` meldet, startet der Container den nächsten Eintrag. Dadurch bleibt die Reihenfolge vollständig unter eigener Kontrolle.

## Noch offen für die Gerätekonfiguration

Die Ende-Erkennung ist absichtlich als Beispiel enthalten, weil Entity-ID, Statuswerte und Attribute vom verwendeten ADB-/MediaSession-Sensor abhängen. Die API und Queue-Logik sind bereits vollständig vorbereitet.
