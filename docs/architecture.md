# Architektur

## Übersicht

SmartTube PartyQueue V4.5 steuert SmartTube primär über die REST API des PartyQueue-SmartTube-Forks.

```text
Browser (Gast / Host)
        |
        v
PartyQueue (FastAPI + SQLite + WebSocket)
        |
        +-- SmartTube REST API :8090
        |     Playback State, Play/Pause/Seek/Next, Queue
        |
        +-- SmartTube Event API (optional)
        |     video_started, video_ended, user_skip, sponsorblock_skip
        |
        +-- ADB Bootstrap/Fallback
              startet SmartTube nur, wenn die REST API nicht verfügbar ist
```

## Playback

- REST ist die laufende Status- und Steuerquelle.
- PartyQueue hält in SmartTube `current + next + reserve` bereit.
- Queue-Matching verwendet die Reihenfolge des REST-`items`-Arrays; das eingebettete `index`-Feld wird nach Mutationen nicht als alleinige Wahrheit verwendet.
- Der aktuell laufende Titel wird niemals erneut als Prefetch-Kandidat angelegt.
- SmartTube-Events verbessern Ende-/Skip-Erkennung, sind aber für den REST-Betrieb nicht erforderlich.
- ADB ist kein normaler Playback-Transport mehr. Es dient nur zum Start/Recovery von SmartTube bei ausgefallener REST API.

## MultiSync

Der Standard-TV ist der Lead. Follower erhalten dasselbe logische Queue-Fenster und werden bei Video- oder Positionsabweichungen über die SmartTube REST API korrigiert. Nur der Lead darf Queue-/Historienentscheidungen auslösen.

## Persistenz

- `/app/data`: SQLite-Datenbank und Banner
- `/root/.android`: persistente ADB-Schlüssel für Bootstrap/Fallback
