## Konfigurationsreferenz

SmartTube PartyQueue V3 verwendet die `.env` nur noch für die Bootstrap-Konfiguration des Containers. TVs sowie YouTube-, Home-Assistant-, Such-, Playback- und Diagnoseeinstellungen werden in der Host-WebUI gepflegt und in SQLite gespeichert.

### Bootstrap-Konfiguration

```bash
cp .env.example .env
```

```env
ADMIN_PASSWORD=change-me
DATA_DIR=/app/data
```

- `ADMIN_PASSWORD`: Passwort für die Hostoberfläche und geschützten Admin-API-Endpunkte. Vor dem ersten Start ändern.
- `DATA_DIR`: Persistentes Datenverzeichnis im Container. Beim Standard-Compose-Setup `/app/data`.

### Einstellungen in der WebUI

Nach dem Start unter **Host → Einstellungen** konfigurieren:

- YouTube API Key
- Zeitzone
- Home-Assistant URL und Webhook-ID, falls der optionale HA-Transport verwendet wird
- SmartTube-Paketname
- Such- und Kontingentgrenzen
- Playlist-Wiederholungsschutz
- Ende-, Idle-, Skip-, Watchdog- und ADB-Parameter

Diese Werte liegen in `settings_store` der SQLite-Datenbank. Werte aus einer alten `.env` werden nicht mehr als dokumentierter Konfigurationsweg unterstützt.

### Geräte

TVs werden ausschließlich unter **Host → TVs** angelegt. Pro Gerät werden ID, Anzeigename, Host/IP, Transportmodus, Aktivstatus und Standardstatus in SQLite gespeichert. Für ADB-Geräte stehen Pairing und Verbindungstest direkt in der WebUI bereit.

Die früheren Variablen `DEFAULT_TV` und `TV_DEVICES` wurden entfernt. Eine neue Installation startet ohne vorkonfigurierte Geräte. Zuerst einen TV anlegen, anschließend eine Party erstellen.

### Persistenz

```yaml
volumes:
  - ./data:/app/data
  - ./adb:/root/.android
```

`./data` enthält SQLite. `./adb` enthält die privaten ADB-Schlüssel. Beide Verzeichnisse sichern; `./adb` niemals veröffentlichen oder committen.
