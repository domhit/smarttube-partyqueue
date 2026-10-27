# SmartTube PartyQueue V4.4.3-alpha1

Entwicklungsstand auf Basis von V4.4.2 Stable. V4 verwendet die SmartTube-REST-API und die native SmartTube-Queue für lückenarme Titelübergänge, Recovery und optionalen MultiSync-Betrieb.

## Neuerungen in V4.4.3-alpha1

### TV-Health-Ampel

Der TV-Tab aktualisiert alle 10 Sekunden den Zustand jedes Geräts:

- **Grün:** REST erreichbar; bei aktiver Wiedergabe stimmen erwarteter und tatsächlich laufender Titel überein und die Queue ist ausreichend aufgebaut.
- **Gelb:** REST erreichbar, aber Player idle, Titel abweichend, Playerstatus unklar oder aktive Queue unvollständig.
- **Rot:** SmartTube-REST-API nicht erreichbar.
- **Grau:** TV deaktiviert.

REST- und ADB-Einzeltests bleiben zusätzlich verfügbar. Die automatische Health-Prüfung führt bewusst keinen dauernden ADB-Connect aus.

### Automatisierte Regressionstests

Bei Pushes und Pull Requests prüft GitHub Actions automatisch:

- Python-Syntax
- JavaScript-Syntax
- Queue-Prefetch `current + next + reserve`
- MultiSync-Video-Mismatch und Driftkorrektur
- Foreground-Recovery nach einem erreichbaren, aber inaktiven SmartTube-Player
- Schutz vor dem fälschlichen Leeren der Queue bei `idle` während eines Startversuchs
- TV-Health-Klassifizierung
- Docker-Build als Smoke-Test

Das GHCR-Image wird erst veröffentlicht, wenn diese Tests erfolgreich sind.

## Empfohlene SmartTube-Einstellungen

- **Allgemein → Hintergrundwiedergabe:** Bild-in-Bild bei Home/Back aktivieren
- **Player → Wiedergabemodus:** Videos fortlaufend abspielen
- **Player → Pause nach jedem Video:** deaktivieren
- **Player → Stop nach jedem Video:** deaktivieren
- **Player → Netzwerk-Engine:** Cronet

Video-, Audio-, Codec-, HDR- und Decoder-Voreinstellungen sollten wegen unterschiedlicher Hardware geräteabhängig bleiben.

## Persistente Daten

```yaml
volumes:
  - ./data:/app/data
  - ./adb:/root/.android
```

`adb/` enthält private ADB-Schlüssel und darf nicht veröffentlicht oder committed werden.
