# Fehlerbehebung

## Health-Endpunkt

```bash
curl http://127.0.0.1:8787/api/health
```

## Containerlogs

```bash
docker compose logs --tail=200 -f
```

## Playback-Diagnose sichern

Im Debug-Tab `JSON kopieren` verwenden oder:

```bash
docker compose logs --since=10m \
  | grep PLAYBACK_DEBUG \
  > playback-debug.log
```

## Wichtige Diagnoseereignisse

| Ereignis | Bedeutung |
|---|---|
| `PLAY_DISPATCHED` | Startanforderung wurde asynchron ausgeloest |
| `PLAY_REQUEST` | Home-Assistant-Aufruf wurde gestartet |
| `PLAY_WEBHOOK_OK` | Home Assistant hat geantwortet |
| `PLAY_WEBHOOK_TIMEOUT` | Home Assistant hat nicht rechtzeitig geantwortet |
| `PLAY_CONFIRM_WAIT` | PartyQueue wartet auf `playing` |
| `PLAY_RETRY` | Startbefehl wird einmal wiederholt |
| `PLAY_CONFIRMED` | SmartTube-Wiedergabe bestaetigt |
| `PLAY_CONFIRM_FAILED` | Beide Startversuche blieben unbestaetigt |
| `EXTERNAL_SKIP_DETECTED` | Externer SmartTube-Skip erkannt |
| `END_DETECTED` | Titelende ueber Dauer-Schwelle erkannt |
| `IDLE_TIMER_SCHEDULED` | Idle-Fallback wurde geplant |
| `IDLE_IGNORED_GUARD` | Uebergangs-Idle wurde ignoriert |
| `DONE` | Queue-Eintrag abgeschlossen |

## SmartTube startet nicht

Pruefen:

1. Ist der Ziel-TV in Home Assistant erreichbar?
2. Funktioniert `androidtv.adb_command` manuell?
3. Stimmt `SMARTTUBE_PACKAGE`?
4. Stimmen PartyQueue-TV-ID und Automation-Trigger-ID ueberein?
5. Erscheint `PLAY_WEBHOOK_OK`?
6. Erscheint danach `PLAY_CONFIRMED` oder `PLAY_RETRY`?

## Host zeigt "Noch nichts"

Das ist normal, wenn kein Queue-Eintrag den Status `playing` hat. Bei einem Fehler den Debug-Tab ab `DONE` bis `PLAY_CONFIRMED` beziehungsweise `PLAY_CONFIRM_FAILED` kopieren.

## Skip-Kaskade

Eine Skip-Kaskade sollte durch den Start-Guard verhindert werden. Erwartet wird nach einem neuen Titelstart:

```text
START_GUARD_ARMED
PLAY_REQUEST
IDLE_IGNORED_GUARD
```

Wenn stattdessen direkt `DONE reason=idle_fallback` fuer den neuen Titel erscheint, Diagnose-JSON und Dockerlogs sichern.

## SponsorBlock am Videoende

Ein SponsorBlock-Sprung kann den Player direkt nach `idle` versetzen. Der erwartete Recovery-Ablauf ist:

```text
DONE reason=idle_fallback
NEXT_QUEUE_SELECTED oder NEXT_BASE_SELECTED
PLAY_DISPATCHED
PLAY_REQUEST
PLAY_CONFIRM_WAIT
PLAY_RETRY (nur wenn erforderlich)
PLAY_CONFIRMED
```

## YouTube-Suche funktioniert nicht

- `YOUTUBE_API_KEY` pruefen.
- Im Host den Kontingentbereich kontrollieren.
- `YOUTUBE_SEARCH_HARD_STOP_AT` pruefen.
- Containerlogs nach API-Fehlern durchsuchen.

## PDF-Export funktioniert nicht

- Image mit `--build` neu bauen.
- Pruefen, ob `reportlab` installiert wurde.
- Containerlogs beim Export beobachten.

```bash
docker compose down
docker compose up -d --build
```

## Datenbank sichern

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
```
