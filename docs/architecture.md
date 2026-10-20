# Architektur

## V2.8.3

```text
Browser
  ├── Gastoberflaeche
  └── Hostoberflaeche
          |
          v
FastAPI-Anwendung
  ├── REST API
  ├── WebSocket State Broadcast
  ├── Playback Engine
  ├── Party-/Playlist-Logik
  ├── Exporte
  └── SQLite
          |
          v
Home Assistant
  ├── Webhook fuer SmartTube-Starts
  ├── ADB-Service
  └── MediaSession-Automation
          |
          v
Android TV / Fire TV / SmartTube
```

## Persistenz

SQLite speichert unter anderem:

- Partys
- Queue und Verlauf
- Playlists und Playlist-Eintraege
- Upvotes
- Hype-Votes
- Basisplaylist-Historie
- YouTube-Kontingentdaten

## Playback State Machine

Wichtige Zustaende:

- `queued`
- `playing`
- `played`
- `skipped`
- `cancelled`

Wichtige Mechanismen:

- Vorzeitige Ende-Erkennung
- Idle-Fallback
- Externe Skip-Erkennung
- Start-Guard
- Playback-Watchdog
- Einmaliger Retry

## Zielarchitektur V3.0

```text
Browser
  |
  v
PartyQueue Standalone
  ├── WebUI
  ├── SQLite
  ├── direkte ADB-Verbindungen
  ├── MediaSession-Auswertung
  ├── TV-Verwaltung
  ├── Playback Engine
  └── REST/WebSocket API
          |
          v
Android TV / Fire TV / SmartTube

Optional:
Home Assistant -> PartyQueue API fuer Dashboard und Automationen
```

Ziel ist die Umkehr der Abhaengigkeit: PartyQueue soll ohne Home Assistant laufen; Home Assistant darf PartyQueue optional konsumieren.
