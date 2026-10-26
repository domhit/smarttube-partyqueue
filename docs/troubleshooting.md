# Troubleshooting V4.4.2

## Healthcheck

```bash
curl http://<partyqueue-host>:8000/api/health
```

Erwartet:

```json
{"ok":true,"version":"4.4.2"}
```

## TV-Diagnose

Unter **Host → TVs** für jedes Gerät prüfen:

- REST erreichbar
- ADB erreichbar und autorisiert

ADB ist für den normalen REST-Betrieb nicht dauerhaft erforderlich, wird aber für Bootstrap und Foreground-Recovery benötigt.

## SmartTube läuft, bleibt aber idle oder unsichtbar

V4.4.2 erkennt den Fall, dass die REST-API erreichbar ist, aber nach einem erfolgreichen `/play` kein aktiver Titel bestätigt wird. PartyQueue versucht anschließend eine Foreground-Recovery über ADB und öffnet den erwarteten Titel erneut sichtbar in SmartTube.

Relevante Diagnoseereignisse:

```text
PLAY_PENDING_IDLE
FOREGROUND_RECOVERY_REQUIRED
FOREGROUND_RECOVERY_STARTED
PLAY_CONFIRMED_AFTER_FOREGROUND_RECOVERY
FOREGROUND_RECOVERY_FAILED
```

## ADB meldet offline oder unauthorized

Am TV ADB-/USB-Debugging aktivieren und die Autorisierungsabfrage bestätigen. Danach den ADB-Test im TV-Tab erneut ausführen.

Persistente ADB-Schlüssel liegen im gemounteten `adb/`-Verzeichnis.

## Queue enthält nicht current + next + reserve

Im vollständigen Playback-Debug auf folgende Ereignisse achten:

```text
QUEUE_PREFETCHED
QUEUE_WINDOW_READY
QUEUE_PREFETCH_ERROR
```

Ein gesunder Zustand enthält in SmartTube normalerweise drei Einträge: den aktuellen Titel sowie zwei vorbereitete Folgetitel.

## MultiSync

Lead und Follower sollten dieselbe SmartTube-Queue haben. Bei abweichender Video-ID versucht PartyQueue einen Videoabgleich und anschließend bei Bedarf eine Positionskorrektur.

Relevante Ereignisse:

```text
SYNC_VIDEO_MISMATCH
SYNC_VIDEO_SWITCH
SYNC_VIDEO_CONFIRMED
SYNC_DRIFT_SEEK
```

Auf allen MultiSync-Geräten sollten `Pause nach jedem Video` und `Stop nach jedem Video` deaktiviert sowie fortlaufende Wiedergabe aktiviert sein.

## Datenbank sichern

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
```
