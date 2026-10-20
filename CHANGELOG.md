# Changelog

Alle wesentlichen Aenderungen an SmartTube PartyQueue werden in dieser Datei dokumentiert.

Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/) und die Versionierung an [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Fixed
- V3.0.0-alpha4.1: MediaSession-RegEx korrigiert; PlaybackState wird jetzt gezielt aus `PlaybackState {state=..., position=...}` gelesen.

### Added
- V3.0.0-alpha4: Direktes ADB-Monitoring für playing, paused, idle und Position über `dumpsys media_session`.
- ADB-TVs benötigen für Playback und Status kein Home Assistant mehr.
- Konfigurierbares ADB-Abfrageintervall und neue Diagnoseevents.
- V3.0.0-alpha3: Wiedergabestart wahlweise über Home Assistant oder direkt per ADB pro TV.
- ADB-Transport mit Connect, SmartTube VIEW-Intent, Watchdog-Retry und Diagnoseevents.
- Stabile alphabetische TV-Liste ohne Sprung beim Wechsel des Standardgeräts.
- V3.0.0-alpha2: Host statt IP, direkter Standardgerät-Radiobutton, Aktiv-Schalter und ADB-Verbindungstest.
- V3.0.0-alpha1: TV- und Laufzeiteinstellungen in SQLite.
- Neue Host-Tabs fuer TV-Verwaltung und Einstellungen.
- Einmaliger Import der bestehenden `.env`-Werte.

### Geplant

- Standalone-Core mit direkter ADB-Anbindung
- TV-Verwaltung in der WebUI
- Home Assistant als optionale Integration
- GitHub Container Registry und Portainer-Deployment

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
