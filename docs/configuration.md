# Konfigurationsreferenz

## Bootstrap-Konfiguration (.env)

```text
ADMIN_PASSWORD=change-me
DATA_DIR=/app/data
```

Alle Playback-, SmartTube-, YouTube- und TV-Einstellungen werden anschließend unter **Host -> Einstellungen** bzw. **Host -> TVs** gepflegt und in SQLite gespeichert.

## TVs

Pro Gerät werden gespeichert:
- interne PartyQueue-ID
- Anzeigename
- Host/IP
- SmartTube REST-Port (Standard `8090`)
- REST-Benutzer und Passwort
- Aktiv-/Standardstatus

REST ist der primäre Transport. Unter **TVs -> REST testen** lässt sich die Verbindung prüfen.

## ADB Bootstrap/Fallback

ADB wird nicht für den normalen Playback-Status verwendet. Es startet SmartTube bei einem REST-Ausfall und benötigt deshalb weiterhin das persistente Volume:

```yaml
- ./adb:/root/.android
```

Einstellungen: Bootstrap aktiv, ADB-Port, Grace-Zeit, Ready-Timeout, Cooldown und SmartTube-Paketname.

## SmartTube Event API

Optional kann SmartTube Ereignisse an PartyQueue pushen. Unter **Host -> Einstellungen** einen gemeinsamen **SmartTube Event Token** setzen. In SmartTube werden eingetragen:
- PartyQueue-URL, z. B. `http://192.168.1.10:8787`
- Device-ID exakt passend zur internen PartyQueue-TV-ID
- derselbe Event-Token

SmartTube verwendet `/api/smarttube/event` und `/api/smarttube/event/health`.

## Queue Prefetch

`queue_prefetch_interval` steuert den Abgleich von `next + reserve`. Das aktuell laufende Video wird nicht erneut als Kandidat verwendet. Nach Queue-Adds wartet PartyQueue kurz auf die aktualisierte SmartTube-Queue.
