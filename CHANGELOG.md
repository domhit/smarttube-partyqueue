# Changelog

Alle wesentlichen Aenderungen an SmartTube PartyQueue werden in dieser Datei dokumentiert.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und die Versionierung an [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Changed

- `.env.example` auf `ADMIN_PASSWORD` und `DATA_DIR` als reine Bootstrap-Konfiguration reduziert.
- TVs und Laufzeiteinstellungen werden ausschließlich über WebUI und SQLite verwaltet.
- Neue Installationen starten ohne persönliche oder Demo-TV-Einträge.
- README und Konfigurationsdokumentation auf den Standalone-Einrichtungsablauf aktualisiert.

### Added

- GitHub-Actions-Workflow für Multi-Arch-Builds und Veröffentlichung in GHCR.
- Build-Provenance, SBOM und GitHub-Actions-Buildcache.

### Removed

- Legacy-Umgebungsvariablen `DEFAULT_TV` und `TV_DEVICES`.
- Gerätespezifische Standardwerte und Home-Assistant-Beispiele.
- Automatische Erstellung einer Standard-Party aus Env-Gerätelisten.


## [3.0.0-beta1] - 2026-10-20

### Added

- Direkte ADB-Wiedergabe ohne Home Assistant
- Direkte MediaSession-Auswertung über `dumpsys media_session`
- TV-Verwaltung vollständig in SQLite
- Laufzeiteinstellungen vollständig in SQLite
- TV-Management über die Weboberfläche
- ADB-Verbindungstest je TV
- Auswahl des Transportlayers pro Gerät:
  - Home Assistant
  - Direktes ADB
- Persistente Speicherung der ADB-Schlüssel über `/root/.android`
- Konfigurierbares ADB-Abfrageintervall
- Erweiterte Playback-Diagnose für ADB- und Home-Assistant-Transport

### Changed

- Home Assistant ist für die Wiedergabesteuerung nicht mehr erforderlich
- Geräte werden nicht mehr aus `TV_DEVICES` verwendet, sondern aus der SQLite-Datenbank
- Laufzeiteinstellungen werden nicht mehr aus der `.env` verwendet, sondern aus der SQLite-Datenbank
- TV-Verwaltung erfolgt über die WebUI
- Wiedergabestatus kann direkt über Android MediaSession gelesen werden

### Fixed

- Direkte Erkennung von SmartTube-Skips
- SponsorBlock-Sprünge werden korrekt verarbeitet
- PLAY_CONFIRM-Watchdog arbeitet mit ADB und Home Assistant
- Externe Skip-Erkennung bei Positionsrücksetzung
- Enderkennung über Videodauer
- Enderkennung über Idle-Fallback
- Start-Guard gegen Skip-Kaskaden
- Wiedergabe-Recovery nach fehlgeschlagenen Starts
- Persistente ADB-Berechtigungen bei Container-Rebuilds

### Status

- Mehrere reale Geräte erfolgreich getestet
- Xiaomi Android TV erfolgreich ohne Home Assistant betrieben
- First Standalone ADB Beta
  
### Geplant

- TV-Verwaltung in der WebUI mit TV-Editor statt Prompt-Dialog
- ADB Pairing/Connect direkt in der WebUI
- GHCR (GitHub Container Registry)
- Portainer-Deployment
- Home Assistant als optionale Integration dokumentieren
- Beta-Test auf allen verfügbaren Geräten

## [2.8.3] - 2026-10-19

### Fixed

- Playback-Watchdog startet unabhaengig vom Home-Assistant-Webhook.
- Haengende Webhook-Aufrufe blockieren den automatischen Retry nicht mehr.
- SponsorBlock-Spruenge am Videoende koennen die Playlist automatisch fortsetzen.
- Eigener Timeout fuer einzelne Home-Assistant-Aufrufe.

### Added

- Diagnoseereignisse `PLAY_DISPATCHED` und `PLAY_WEBHOOK_TIMEOUT`.

## [2.8.2] - 2026-10-19

### Added

- Pflichtname vor dem Einreichen eines Musikwunschs.
- Hype-Button fuer den laufenden Titel.
- Hype-Auswertung in Host, Archiv, HTML-Recap und PDF-Recap.
- Playback-Watchdog mit Startbestaetigung und einmaligem Retry.

## [2.8.1] - 2026-10-19

### Changed

- Verlauf zeigt die aktuell ausgewaehlte Zielplaylist im Button.
- Playlist-Auswahldialog mit Titelanzahl, Hervorhebung und Abbrechen.

## [2.8.0] - 2026-10-19

### Added

- Archivsuche.
- Erweiterte Archivstatistiken.
- Sicheres Loeschen archivierter Partys.
- PDF-Recap mit Statistiken, Ranking und Playlist.

## [2.7.2] - 2026-10-19

### Added

- Host-Tabs fuer Party, Playlist, Archiv und Debug.
- Speicherung des zuletzt ausgewaehlten Tabs.
- Debug-Polling nur bei geoeffnetem Debug-Tab.

## [2.7.1] - 2026-10-19

### Fixed

- Start-Guard verhindert Skip-Kaskaden durch verzoegerte `idle`-Meldungen.

### Added

- Playback-Diagnosepanel mit strukturierten Ereignissen.

## [2.7.0] - 2026-10-19

### Added

- Neue Party, Party klonen und Party abschliessen.
- Partyarchiv.
- HTML-Party-Recap.
- CSV-, JSON- und M3U-Export.

## [2.6.0] - 2026-10-19

### Added

- Vollstaendige Playlist-Verwaltung.
- Filter, Gesamtdauer und Aktivstatus.
- Kopieren und Verschieben zwischen Playlists.
- Drag-and-drop fuer Playlists und Queue.

## [2.5.2] - 2026-10-19

### Added

- UI-Schalter fuer externe Skip-Erkennung.
- YouTube-API-Kontingent in der Hostansicht.
- Duplikat- und Wiederholungsschutz pro Ziel-TV.
- Verbessertes Tampermonkey-Userscript.

## [2.5.1]

### Stable

- Letzter verifizierter Ausgangsstand der Playback- und Skip-Engine vor dem schrittweisen Neuaufbau.

## Fruehe Versionen

- Host- und Gastoberflaeche
- YouTube-Suche und URL-Import
- Wunschqueue und Upvotes
- SmartTube-/Home-Assistant-Anbindung
- Multi-TV-Unterstuetzung
