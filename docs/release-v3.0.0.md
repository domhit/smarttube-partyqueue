# SmartTube PartyQueue V3.0.0

V3.0.0 ist der erste stabile Standalone-Release von SmartTube PartyQueue.

## Highlights

- direkte ADB-Wiedergabe ohne Home Assistant
- direkte Android-MediaSession-Auswertung
- TV-Editor, ADB-Pairing und Verbindungstest in der WebUI
- SQLite-basierte Geräte- und Laufzeitkonfiguration
- mobile Gastoberfläche und Partybanner
- Multi-TV-Queues, Playlists, Upvotes und Hypes
- Partyarchiv und Exporte
- GHCR-Multi-Arch-Images und Portainer-Deployment

## Validierung

Der Release basiert auf einem Dauertest von mehr als 20 Stunden sowie erfolgreichen Tests auf fünf Zielgeräten. Dabei wurden Wunschqueues, Gerätewechsel und ein Container-Neustart während einer laufenden Party geprüft.

## Upgrade von V2.8.3

Vor dem Upgrade ein Backup erstellen. V3 verwaltet TVs und Laufzeiteinstellungen in SQLite. `DEFAULT_TV` und `TV_DEVICES` werden nicht mehr verwendet.

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
docker compose pull
docker compose up -d
```

Nach dem Upgrade TVs und Einstellungen in der Hostoberfläche kontrollieren. ADB-Schlüssel müssen über das persistente Volume `./adb:/root/.android` erhalten bleiben.
