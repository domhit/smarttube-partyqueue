# Changelog

Alle wesentlichen Änderungen an SmartTube PartyQueue werden hier dokumentiert. Das Format orientiert sich an Keep a Changelog und die Versionierung an Semantic Versioning.

## [Unreleased]

## [4.4.3-alpha5] - 2026-10-27

### Fixed
- geplante SmartTube-Übergänge auf den nächsten PartyQueue-Titel werden adoptiert statt zurückgewiesen
- fremde Live-Titel werden weiterhin durch den erwarteten PartyQueue-Titel ersetzt
- Queue-Recovery erhält eine sechssekündige Cooldown-Phase
- MultiSync wartet während einer laufenden Queue-Recovery
- veraltete Alpha2-Tests wurden entfernt

## [4.4.3-alpha5] - 2026-10-27

### Added

- Live-State-Reconciliation zwischen SmartTube-Wiedergabe und PartyQueue-Datenbank nach drei stabilen REST-Polls
- unbekannte externe Live-Titel werden sichtbar angezeigt und dürfen fertiglaufen; anschließend übernimmt PartyQueue wieder die Titelauswahl
- Health-Hysterese: kurze REST-Ausfälle bleiben gelb, Rot erst nach 15 Sekunden durchgehendem Ausfall

### Changed

- Party- und Gastansicht bevorzugen aktuelle REST-Liveinformationen gegenüber einem veralteten DB-Titel
- TV-Health verwendet vorhandene Polling- und Queue-Daten und erzeugt keine zusätzlichen REST-Abfragen

## [4.3.0-alpha1] - 2026-10-21

### Added

- optionaler Multi-TV-Sync pro Party
- Standard-TV als Lead für Wiedergabe, Pause, Fortsetzen, Skip- und Ende-Erkennung
- paralleler Videostart auf allen freigegebenen TVs
- Spiegelung von Pause und Fortsetzen auf ADB-Follower
- Drift-Erkennung sowie Soft-Korrektur für vorauslaufende Follower
- Diagnoseereignisse für Sync-Zustand und Drift
- konfigurierbare Drift-Toleranz und Resume-Marge

### Changed

- TV-Auswahl auf der Gastseite wird bei nur einem Gerät oder aktivem Multi-TV-Sync ausgeblendet

### Known limitations

- Zurückliegende Follower werden erkannt und protokolliert, aber nicht automatisch vorgespult. Android stellt über die verwendete ADB-Schnittstelle keinen zuverlässigen, app-unabhängigen Seek-Befehl bereit.


## [3.0.0] - 2026-10-21

### Added

- direkter ADB-Transport für SmartTube ohne Home Assistant
- direkte MediaSession-Auswertung über `dumpsys media_session`
- TV-Editor, ADB-Pairing und Verbindungstest in der WebUI
- SQLite-basierte TV- und Laufzeitkonfiguration
- mobile Gastoberfläche mit großen Touchflächen und Ergebnis-Karten
- Absenden von Suche und YouTube-Link per Enter
- optionaler Partybanner-Upload für JPG, PNG und WebP bis 5 MB
- GHCR-Multi-Arch-Builds für `linux/amd64` und `linux/arm64`
- Portainer- und Compose-Deployment ohne lokalen Build
- Build-Provenance, SBOM und GitHub-Actions-Buildcache

### Changed

- Home Assistant ist optional und nicht mehr Voraussetzung
- TVs und Laufzeiteinstellungen werden über WebUI und SQLite verwaltet
- externe SmartTube-Skip-Erkennung ist dauerhaft aktiv
- Suchergebnisanzahl und Mindestlänge werden aus den Laufzeiteinstellungen angewendet
- neue Installationen starten ohne persönliche oder Demo-TV-Einträge

### Removed

- Legacy-Umgebungsvariablen `DEFAULT_TV` und `TV_DEVICES`
- gerätespezifische Standardwerte
- automatische Standard-Party aus Env-Gerätelisten

### Validated

- mehr als 20 Stunden Dauertest
- fünf Zielgeräte erfolgreich getestet
- Wunschqueues und Gerätewechsel getestet
- Container-Neustart während laufender Party getestet

## [3.0.0-beta3] - 2026-10-21

- mobile Gastoberfläche, Enter-Unterstützung und Partybanner
- Suchlimit-Korrektur und dauerhaft aktive Skip-Erkennung

## [3.0.0-beta2] - 2026-10-21

- TV-Editor, ADB-Pairing, GHCR und Portainer-Deployment

## [3.0.0-beta1] - 2026-10-20

- erster Standalone-ADB-Betastand
- direkte Wiedergabe, MediaSession-Auswertung und Playback-Diagnose

## [2.8.3] - 2026-10-19

- letzter stabiler V2-Release mit verpflichtender Home-Assistant-Anbindung
- Playback-Watchdog unabhängig vom Webhook
- Recovery nach SponsorBlock-Sprüngen

## Ältere Versionen

Siehe Git-Tags und die Release-Historie des Repositorys.
