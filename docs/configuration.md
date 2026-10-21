# Konfigurationsreferenz

## Bootstrap-Konfiguration

Die `.env` enthält nur Werte, die vor dem Start des Containers verfügbar sein müssen:

```env
ADMIN_PASSWORD=change-me
DATA_DIR=/app/data
```

- `ADMIN_PASSWORD`: Passwort für Hostoberfläche und geschützte Admin-API
- `DATA_DIR`: persistentes Datenverzeichnis im Container

## Laufzeiteinstellungen

Nach dem Start unter **Host → Einstellungen** verwalten:

- YouTube API Key
- Zeitzone
- SmartTube-Paketname
- maximale Videolänge
- maximale offene Wünsche je Gast
- Suchcache, Mindestlänge und Ergebnisanzahl
- YouTube-Kontingentgrenzen
- Wiederholungsschutz
- Ende-, Idle-, Skip- und Watchdog-Parameter
- ADB-Abfrageintervall
- Home-Assistant URL und Webhook-ID für den optionalen HA-Transport

Die Werte werden in `settings_store` der SQLite-Datenbank gespeichert und nach dem Speichern unmittelbar angewendet.

## TVs

TVs werden ausschließlich unter **Host → TVs** verwaltet. Pro Gerät werden gespeichert:

- interne ID
- Anzeigename
- Host oder IP-Adresse
- Transportmodus `adb` oder `ha`
- optionale Home-Assistant MediaSession-Entity
- Aktivstatus
- Standardstatus

Die früheren Variablen `DEFAULT_TV` und `TV_DEVICES` sind entfernt.

## Partybanner

Für die aktive Party kann ein JPG-, PNG- oder WebP-Bild bis 5 MB hochgeladen werden. Die Datei liegt unter `/app/data/banners` und wird über `/banners/...` ausgeliefert.

## Volumes

```yaml
volumes:
  - ./data:/app/data
  - ./adb:/root/.android
```

- `data`: Datenbank, Banner und weitere persistente Anwendungsdaten
- `adb`: private ADB-Schlüssel

Beide Verzeichnisse sichern. `adb` niemals veröffentlichen oder committen.
