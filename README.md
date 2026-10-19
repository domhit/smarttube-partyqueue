# SmartTube PartyQueue V2.7.1-debug1

Diagnose-Build auf Basis des produktiv getesteten V2.7.0-Stands. Party-Lifecycle, Archiv, Recap, Playlist-Verwaltung und Multi-TV bleiben erhalten. Die Playback-Entscheidungen werden zusätzlich protokolliert und im Host-Frontend dargestellt.

## Playback-Diagnosepanel

Nach der Anmeldung im Host erscheint die Karte **Playback-Diagnose** mit:

- internem Status je TV
- letzter Position und Alter der Statusmeldung
- aktueller App-ID
- verbleibendem Guard-Zeitraum
- aktivem Idle-Timer
- TV-Filter
- Live-Aktualisierung alle 1,5 Sekunden
- manuellem Aktualisieren
- Kopieren aller Diagnosedaten als JSON
- Leeren des In-Memory-Protokolls

Die letzten 500 Events werden nur im Arbeitsspeicher gehalten und gehen beim Container-Neustart verloren.

## Ereignisse

- `PROGRESS`: eingehende Home-Assistant-Meldung
- `DECISION`: Ergebnis der Ende- und Skip-Prüfung
- `DECISION_SKIPPED`: Meldung passt nicht zu State/App
- `END_DETECTED`: Ende über Dauer-Schwelle erkannt
- `EXTERNAL_SKIP_DETECTED`: Positionssprung als externer Skip erkannt
- `IDLE_TIMER_SCHEDULED`, `IDLE_TIMER_FIRED`, `IDLE_TIMER_CANCELLED`, `IDLE_IGNORED_GUARD`
- `DONE`: Queue-Eintrag abgeschlossen, inklusive Grund
- `NEXT_ENTER`, `NEXT_BLOCKED_PLAYING`, `NEXT_QUEUE_SELECTED`, `NEXT_BASE_SELECTED`, `NEXT_NO_ITEM`
- `PLAY_REQUEST`, `PLAY_WEBHOOK_OK`, `PLAY_WEBHOOK_ERROR`
- `MANUAL_SKIP_BUTTON`

Dieselben Events werden als strukturierte JSON-Zeilen mit Präfix `[PLAYBACK_DEBUG]` in die Docker-Logs geschrieben.

## Fehler reproduzieren

1. Host öffnen und anmelden.
2. Im Diagnosepanel den betroffenen TV auswählen.
3. Diagnose leeren.
4. Checkbox **Externe Skip-Erkennung** auf den gewünschten Zustand setzen und **Party speichern** drücken.
5. Einen einzelnen Testfall ausführen: SmartTube-Skip, Host-Skip, natürliches Ende oder Pause.
6. Sobald der Fehler auftritt, **Live** deaktivieren.
7. **JSON kopieren** drücken und den Inhalt zur Analyse bereitstellen.

Parallel können die Serverlogs gespeichert werden:

```bash
docker compose logs --since=10m smarttube-partyqueue | grep PLAYBACK_DEBUG > playback-debug.log
```

## Installation

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
docker compose logs --tail=100 -f
```

Keine Änderung an `.env`, Datenbank, Home Assistant oder Caddy erforderlich.
