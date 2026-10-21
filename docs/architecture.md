# Architektur

## Übersicht

```text
Gast- und Host-Browser
        |
        v
SmartTube PartyQueue
FastAPI + REST + WebSocket
        |
        +-- SQLite: Partys, Queue, Playlists, Geräte, Einstellungen
        +-- ADB: Wiedergabestart, Pairing, MediaSession-Abfrage
        +-- Export: HTML, PDF, CSV, JSON, M3U
        |
        v
Android TV / Fire TV / SmartTube
```

Home Assistant ist optional und kann je TV anstelle des direkten ADB-Transports verwendet werden.

## Komponenten

- **FastAPI:** REST-Endpunkte, WebSocket, statische Weboberflächen und Exporte
- **SQLite:** persistente Anwendungsdaten unter `/app/data/partyqueue.db`
- **ADB:** Gerätekopplung, Verbindung, SmartTube-Start und MediaSession-Auswertung
- **Gastoberfläche:** Suche, URL-Import, Upvotes, Hypes und Wiedergabestatus
- **Hostoberfläche:** Party-, Playlist-, TV-, Einstellungs-, Archiv- und Debugverwaltung

## Persistenz

`/app/data` enthält:

- SQLite-Datenbank
- hochgeladene Partybanner unter `/app/data/banners`

`/root/.android` enthält:

- `adbkey`
- `adbkey.pub`

Beide Pfade müssen als persistente Volumes eingebunden werden.

## Playback-Zustände

Queue-Einträge verwenden:

- `queued`
- `playing`
- `played`
- `skipped`
- `cancelled`

Wichtige Mechanismen:

- Start-Guard gegen Übergangs-Idle
- Bestätigung des Wiedergabestarts
- einmaliger automatischer Retry
- Ende-Erkennung über Dauer und Position
- Idle-Fallback
- externe Skip-Erkennung
- getrennte Zustände je Ziel-TV

## Transportmodi

### Direktes ADB

PartyQueue verbindet sich mit dem Zielgerät, startet SmartTube per Android-Intent und liest den Wiedergabestatus aus `dumpsys media_session`.

### Home Assistant

PartyQueue sendet den Start über einen Webhook. Home Assistant meldet Wiedergabestatus und Position an `/api/playback/progress`. Dieser Modus bleibt für bestehende Installationen und Sonderfälle verfügbar.
