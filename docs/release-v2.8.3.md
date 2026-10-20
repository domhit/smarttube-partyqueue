# SmartTube PartyQueue V2.8.3

V2.8.3 ist der letzte stabile Release der V2.x-Linie mit verpflichtender Home-Assistant-Anbindung.

## Highlights

- Auf mehreren echten Partys produktiv getestet
- Host- und Gastoberflaeche
- Multi-TV-Queue
- Playlist-Verwaltung
- Party-Lifecycle und Archiv
- Upvotes und Hype
- HTML- und PDF-Recap
- SponsorBlock-Recovery
- Playback-Watchdog mit einmaligem Retry
- Ausfuehrliches Diagnosepanel

## Behoben

Der Playback-Watchdog startet jetzt unabhaengig vom Home-Assistant-Webhook. Ein haengender Webhook kann den automatischen Retry nicht mehr blockieren.

## Upgrade

```bash
git pull
docker compose down
docker compose up -d --build
```

Vor dem Upgrade Backup erstellen:

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
```

## Ausblick

Die V3.0-Entwicklung erfolgt auf `develop` und ersetzt Home Assistant als Pflichtabhaengigkeit durch direkte ADB-Unterstuetzung. Home Assistant bleibt als optionale Integration geplant.
