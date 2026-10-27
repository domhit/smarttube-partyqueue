# Fehlerbehebung

## Health-Endpunkt

```bash
curl http://127.0.0.1:8787/api/health
```

Erwartet:

```json
{"ok":true,"version":"4.3.0-alpha1"}
```

## Containerlogs

```bash
docker compose logs --tail=200 -f
```

Playback-Ereignisse filtern:

```bash
docker compose logs --since=10m | grep PLAYBACK_DEBUG > playback-debug.log
```

## Direktes ADB funktioniert nicht

Prüfen:

- Drahtloses Debugging ist am Zielgerät aktiv.
- Host/IP im TV-Editor ist korrekt.
- Pairing-Code und Pairing-Port stammen aus dem aktuellen Pairing-Dialog des TVs.
- Port 5555 beziehungsweise der vom Gerät angezeigte Verbindungsport ist erreichbar.
- `./adb:/root/.android` ist persistent eingebunden.
- Im Debug-Tab erscheinen `ADB_PAIR`, `ADB_CONNECT`, `ADB_TEST` oder `ADB_POLL_ERROR`.

## SmartTube startet nicht

- Verbindung unter **TVs → Verbinden/Testen** prüfen.
- SmartTube-Paket unter **Einstellungen** prüfen. Standard: `org.smarttube.stable`.
- Im Debug-Tab auf `PLAY_REQUEST`, `PLAY_ADB_OK`, `PLAY_RETRY` und `PLAY_CONFIRM_FAILED` achten.

## Host zeigt „Noch nichts“

Es existiert kein Queue-Eintrag mit Status `playing`. Im Debug-Tab den Ablauf ab `NEXT_QUEUE_SELECTED` oder `NEXT_BASE_SELECTED` prüfen.

## Skip oder Titelende wird nicht erkannt

Relevante Ereignisse:

- `EXTERNAL_SKIP_DETECTED`
- `END_DETECTED`
- `IDLE_TIMER_SCHEDULED`
- `IDLE_IGNORED_GUARD`
- `DONE`

Bei Problemen Diagnose-JSON und Containerlogs gemeinsam sichern.

## YouTube-Suche

- YouTube API Key unter **Host → Einstellungen** prüfen.
- Kontingentanzeige in der Hostoberfläche kontrollieren.
- Such-Mindestlänge und Ergebnisanzahl prüfen.
- Nach Änderung der Ergebnisanzahl werden auch gecachte Ergebnisse auf das neue Limit begrenzt.

## Banner wird nicht angezeigt

```bash
docker exec -it smarttube-partyqueue sh -c "ls -lah /app/data/banners"
```

Zusätzlich prüfen:

- `/app/data` ist persistent eingebunden.
- die Datei ist über `/banners/<dateiname>` erreichbar.
- der Browser wurde hart neu geladen.

## Datenbank sichern

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
```
