# SmartTube PartyQueue V4.4.2

SmartTube PartyQueue ist eine eigenständige Party-Musikqueue mit direkter SmartTube-REST-Steuerung. V4 verwendet die native SmartTube-Queue für vorausgeladene Folgetitel und ermöglicht dadurch weitgehend lückenlose Übergänge ohne erneuten `/play`-Aufruf bei jedem regulären Titelwechsel.

## Aktueller stabiler Stand

V4.4.2 ist der empfohlene Stand für den produktiven Partybetrieb und ersetzt V3 als Hauptentwicklungslinie.

Kernfunktionen:

- REST-only Wiedergabesteuerung über die SmartTube API
- Queue-Fenster aus aktuellem Titel plus zwei Folgetiteln
- Wünsche werden vor automatisch ergänzten Grundplaylist-Titeln priorisiert
- natürliche Queue-Übergänge mit Übernahme des bereits gestarteten Folgetitels
- Skip über SmartTube selbst oder über die Hostoberfläche
- ADB-Bootstrap und Foreground-Recovery bei beendetem oder in den Hintergrund verschobenem SmartTube
- REST- und ADB-Diagnose pro TV
- optionaler MultiSync-Betrieb mit Lead/Follower-Logik, Video-Abgleich und Drift-Korrektur
- Partyarchiv, HTML/PDF-Recaps, Playlists, Votes und Hypes

## Verifizierte Recovery- und Wiedergabeszenarien

Für V4.4.2 wurden erfolgreich getestet:

- normaler automatischer Titelwechsel über die SmartTube-Queue
- Skip direkt in SmartTube
- Skip über die PartyQueue-Hostoberfläche
- SmartTube per Android `force-stop` beenden und automatisch wiederherstellen
- SmartTube über zweimal Back beziehungsweise das TV-Home-Menü in den Hintergrund schicken und automatisch wieder in den Vordergrund holen
- Neustart des PartyQueue-Stacks während laufender Wiedergabe

## Empfohlene SmartTube-Einstellungen

Für einen zuverlässigen Betrieb sollten auf allen PartyQueue-Geräten die wiedergaberelevanten SmartTube-Einstellungen identisch gesetzt werden:

- **Allgemein → Hintergrundwiedergabe:** Bild-in-Bild bei Home/Back aktivieren
- **Player → Wiedergabemodus:** Videos fortlaufend abspielen
- **Player → Pause nach jedem Video:** deaktivieren
- **Player → Stop nach jedem Video:** deaktivieren
- **Player → Netzwerk-Engine:** Cronet

Video-, Audio- und Decoder-Voreinstellungen sollten dagegen geräteabhängig bleiben. Fire TV, Xiaomi TV Stick und unterschiedliche Bravia-/Android-TV-Generationen können unterschiedliche Decoder-, HDR-, Codec- und Audiofähigkeiten besitzen.

Für PartyQueue gilt grundsätzlich:

1. SmartTube soll die vorbereitete Queue selbstständig abarbeiten.
2. PartyQueue überwacht Wiedergabe, Queue und Recovery.
3. ADB dient als Bootstrap- und Recovery-Pfad, wenn REST allein den sichtbaren Player nicht wiederherstellen kann.
4. MultiSync gleicht bei mehreren Geräten Video-ID, Wiedergabezustand und größere Positionsabweichungen ab.

## Deployment

Für produktive Installationen wird das GHCR-Image verwendet. Persistiert werden mindestens:

```yaml
volumes:
  - ./data:/app/data
  - ./adb:/root/.android
```

Das `adb`-Verzeichnis enthält private ADB-Schlüssel und darf nicht veröffentlicht oder committed werden.

Weitere Informationen:

- `docs/configuration.md`
- `docs/troubleshooting.md`
- `docs/migration-v4.md`
- `docs/ghcr.md`
- `CHANGELOG.md`
