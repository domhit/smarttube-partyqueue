# SmartTube PartyQueue V2.8.3

Stabilitäts-Fix auf Basis des produktiv getesteten V2.7.0-Stands. Party-Lifecycle, Archiv, Recap, Playlist-Verwaltung und Multi-TV bleiben erhalten. Die Playback-Entscheidungen werden zusätzlich protokolliert und im Host-Frontend dargestellt.

## Start-Guard-Fix

- Bei jedem von PartyQueue ausgelösten Titelwechsel wird `PRESTART_IDLE_GUARD` aktiviert.
- Alter MediaSession-Status wird verworfen.
- Ein noch laufender Idle-Timer wird abgebrochen.
- Übergangs-`idle` von SmartTube/ADB kann den gerade gestarteten Titel nicht mehr beenden.
- Der Schutz greift bei Host-Skip, extern erkanntem Skip, natürlichem Ende und Idle-Fallback.
- Das Diagnosepanel bleibt zur Verifikation erhalten.

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

## Verifikation des Fixes

Nach einem Host-Skip sollte das Diagnosepanel diese Folge zeigen:

```text
MANUAL_SKIP_BUTTON
DONE reason=host_button
START_GUARD_ARMED
NEXT_QUEUE_SELECTED oder NEXT_BASE_SELECTED
START_GUARD_ARMED reason=play_request
PLAY_REQUEST
PLAY_WEBHOOK_OK
IDLE_IGNORED_GUARD
```

Während der Guard-Zeit darf für den neu gestarteten Titel kein `DONE reason=idle_fallback` erscheinen.


### V2.8.2
- Pflichtname vor Musikwunsch (Frontend und API)
- Hype-Button fuer laufende Titel, ein Toggle pro Gast und Titel
- Hype in Host, Archiv, HTML- und PDF-Recap
- Playback-Start-Watchdog mit einmaligem Retry und Diagnoseevents


### V2.8.3
- Playback-Watchdog startet parallel zum ersten Home-Assistant-Webhook.
- Haengende Webhook-Aufrufe blockieren den Retry nicht mehr.
- Eigener Webhook-Timeout mit `PLAY_WEBHOOK_TIMEOUT=5`.
- Neues Diagnoseereignis `PLAY_WEBHOOK_TIMEOUT`.

#### Technischer Ablauf des V2.8.3-Fixes

```text
PLAY_DISPATCHED + PLAY_CONFIRM_WAIT starten sofort
PLAY_REQUEST attempt=1 laeuft unabhaengig davon
nach 6 Sekunden ohne PLAY_CONFIRMED: PLAY_RETRY attempt=2
jeder Webhook-Versuch endet spaetestens nach PLAY_WEBHOOK_TIMEOUT
nach weiteren 10 Sekunden: PLAY_CONFIRM_FAILED
```

Ein haengender Home-Assistant-Webhook kann den Retry damit nicht mehr blockieren. Der aktuelle Queue-Eintrag bleibt waehrend der Wiederherstellung `playing`; es wird kein weiterer Titel ausgewaehlt.
