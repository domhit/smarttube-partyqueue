# Fehlerbehebung

## Health

```bash
curl http://127.0.0.1:8787/api/health
```

Erwartet: `{"ok":true,"version":"4.5.0-alpha4"}`.

## REST API

Unter **Host -> TVs -> REST testen** prüfen. Standardport des PartyQueue-SmartTube-Forks ist `8090`. Bei Fehlern Host/IP, Port, Benutzer, Passwort und die in SmartTube aktivierte REST API kontrollieren.

## Queue-Prefetch

Relevante Diagnoseereignisse:
- `QUEUE_PREFETCHED`
- `QUEUE_ITEM_REMOVED`
- `QUEUE_WINDOW_READY`
- `QUEUE_PREFETCH_ERROR`

Normal ist `current -> next -> reserve`. `current` darf nicht erneut per Queue-Add eingefügt werden.

## SmartTube startet bei REST-Ausfall nicht

ADB dient nur als Bootstrap/Fallback. Prüfen:
- ADB-Debugging am TV
- ADB-Port und Host/IP
- persistentes `./adb:/root/.android`
- korrektes SmartTube-Paket (Standard dieses Entwicklungsstands: `org.smarttube.beta`)
- Ereignisse `SMARTTUBE_ADB_BOOTSTRAP`, `SMARTTUBE_ADB_VIDEO_START_OK`, `SMARTTUBE_REST_READY`

## Events

Wenn SmartTube Events aktiviert sind, PartyQueue-URL, Device-ID und gemeinsamen Event-Token prüfen. Die Device-ID muss exakt der PartyQueue-TV-ID entsprechen.

## Logs

```bash
docker compose logs --since=10m | grep PLAYBACK_DEBUG > playback-debug.log
```

Im Debug-Tab kann zusätzlich die Diagnose-JSON kopiert werden.
