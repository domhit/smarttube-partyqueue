# SmartTube PartyQueue V2.2

## Neu in V2.2

- 50 YouTube-Suchergebnisse pro API-Suche
- lokale Zählung von Search-Aufrufen, Cache-Treffern und Fehlern
- dynamischer Quota-Reset nach Mitternacht `America/Los_Angeles`
- gemeinsame interne Grundplaylist
- zufällige Grundwiedergabe mit Ausschluss der letzten 20 Grundtitel je TV
- Grundplaylist aus Suche, URL, Verlauf oder öffentlicher YouTube-Playlist befüllen
- Gastwünsche haben Vorrang; danach läuft die Grundplaylist weiter
- Ende-Erkennung über getrennte ADB-MediaSession-Entities (`playing` nach `idle`)
- fünf hinterlegte Zielgeräte

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
```

Die bestehende `.env` bleibt erhalten. Ergänze fehlende Werte aus `.env.example`, insbesondere:

```env
SEARCH_RESULTS=50
SEARCH_CACHE_HOURS=168
YOUTUBE_SEARCH_DAILY_LIMIT=100
YOUTUBE_SEARCH_WARNING_AT=80
YOUTUBE_SEARCH_HARD_STOP_AT=98
BASE_PLAYLIST_RECENT_EXCLUDE=20
```

Danach den Portainer-Stack mit erneutem Build aktualisieren oder:

```bash
docker compose down
docker compose up -d --build
```

Die SQLite-Datenbank wird automatisch erweitert. Vorherige Queue und Historie bleiben erhalten.

## Home Assistant

- `home-assistant/automation.yaml`: Start per fester ADB-Entity-Zuordnung
- `home-assistant/video-ended-example.yaml`: Ende per MediaSession `playing -> idle`
- `home-assistant/rest-command.yaml`: Rückmeldung an den Container

In `rest-command.yaml` die Synology-IP einsetzen und in `secrets.yaml` dasselbe Passwort wie `ADMIN_PASSWORD` hinterlegen.

## Grundplaylist

Die Grundplaylist ist gemeinsam für alle TVs. Jeder TV besitzt jedoch eine eigene Zufallshistorie. Über **Grundmusik starten** beginnt die Wiedergabe auf dem ausgewählten TV. Wenn ein Wunsch eintrifft, läuft der aktuelle Grundtitel zu Ende, danach werden alle Wünsche gespielt und anschließend wieder zufällig aus der Grundplaylist gewählt.

## Quota-Zähler

Gezählt werden ausschließlich von dieser PartyQueue abgesendete `search.list`-Versuche. Cache-Treffer zählen nicht als API-Suche. Wenn derselbe API-Key noch anderweitig verwendet wird, bleibt die Google Cloud Console die maßgebliche Quelle.
