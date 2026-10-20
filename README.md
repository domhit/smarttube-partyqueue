# SmartTube PartyQueue

SmartTube PartyQueue ist eine webbasierte Musik-Wunschliste fuer Partys mit SmartTube auf Android TV und Fire TV. Gaeste reichen ueber eine mobilfreundliche Weboberflaeche Musikwünsche ein, bewerten offene Titel und geben dem aktuell laufenden Song einen Hype. Der Host verwaltet Partys, Warteschlangen, Playlists, Abspieler, Exporte und die Playback-Diagnose ueber eine separate Administrationsoberflaeche.

> **Aktueller stabiler Release:** V2.8.3  
> **Status:** Auf mehreren echten Partys produktiv getestet  
> **Aktuelle Architektur:** Docker + Home Assistant + ADB/Android TV  
> **Geplant fuer V3.0:** Direkte ADB-Anbindung; Home Assistant wird optional

[![Version](https://img.shields.io/badge/version-2.8.3-blue)](CHANGELOG.md)
[![Docker](https://img.shields.io/badge/Docker-supported-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-required%20in%20V2.x-41BDF5?logo=homeassistant&logoColor=white)](docs/home-assistant.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Inhalt

- [Funktionen](#funktionen)
- [Playback und Fehlerbehandlung](#playback-und-fehlerbehandlung)
- [Architektur](#architektur-der-v2x-versionen)
- [Voraussetzungen](#voraussetzungen)
- [Schnellstart](#schnellstart)
- [Konfiguration](#konfiguration)
- [Home Assistant](#home-assistant)
- [Verwendung](#verwendung)
- [Updates und Backups](#updates-und-backups)
- [Diagnose](#diagnose)
- [Versionshistorie](#versionshistorie)
- [Roadmap](#roadmap)

## Screenshots

Die folgenden Dateien koennen unter `docs/screenshots/` abgelegt werden:

| Bereich | Vorgesehene Datei |
|---|---|
| Host - Party | `docs/screenshots/host-party.png` |
| Host - Playlist | `docs/screenshots/host-playlist.png` |
| Gastansicht | `docs/screenshots/guest.png` |
| Partyarchiv | `docs/screenshots/archive.png` |
| HTML-Recap | `docs/screenshots/recap-html.png` |
| PDF-Recap | `docs/screenshots/recap-pdf.png` |

Vor dem Veroeffentlichen sollten Domains, IP-Adressen, API-Schluessel, Passwoerter und unerwuenschte Gastnamen entfernt oder unkenntlich gemacht werden.

## Funktionen

### Gastoberflaeche

- Mobilfreundliche Weboberflaeche
- Namenspflicht vor dem ersten Musikwunsch
- YouTube-Suche ueber die YouTube Data API v3
- Hinzufuegen per YouTube-URL
- Auswahl des Ziel-TVs
- Anzeige des laufenden Titels und Wiedergabefortschritts
- Getrennte Wunschqueue je TV
- Upvotes fuer offene Wuensche
- Hype-Button fuer den aktuell laufenden Titel
- Sperrung neuer Wuensche durch den Host

### Hostoberflaeche

Die Hostoberflaeche ist in vier Tabs gegliedert:

#### Party

- Aktive Party verwalten
- Grundplaylist, erlaubte TVs und Standard-TV konfigurieren
- YouTube-API-Kontingent ueberwachen
- Wiedergabe starten und Titel ueberspringen
- Queue sortieren, priorisieren und Eintraege entfernen

#### Playlist

- Playlists erstellen, umbenennen, duplizieren und loeschen
- Einzelne YouTube-Videos hinzufuegen
- YouTube-Playlists importieren
- Titel aktivieren und deaktivieren
- Titel per Drag-and-drop sortieren
- Titel zwischen Playlists kopieren und verschieben
- Titel aus dem Verlauf in eine frei waehlbare Playlist uebernehmen

#### Archiv

- Abgeschlossene Partys durchsuchen
- Titelanzahl, Wuensche, Upvotes und Laufzeit auswerten
- Top-Wunschgeber, Top-Kuenstler, Top-Vote-Titel und Hype-Titel anzeigen
- HTML-, PDF-, CSV-, JSON- und M3U-Export
- Archivierte Partys mit Namensbestaetigung loeschen

#### Debug

- Playback-Zustaende pro TV
- Wiedergabeposition und App-ID
- Start-Guard und Idle-Fallback
- Startbestaetigung und automatischer Retry
- Strukturierte Diagnoseereignisse
- JSON-Kopie fuer Fehleranalysen

### Party-Lifecycle

- Neue Party starten
- Laufende Party abschliessen
- Party mit ihren Einstellungen klonen
- Offene Wuensche beim Abschluss als `cancelled` archivieren
- Queue, Votes und Verlauf nicht in eine neue Party uebernehmen
- Maximal eine aktive Party gleichzeitig
- Abgeschlossene Partys unveraendert archivieren

### Multi-TV

- Getrennte Queue und Wiedergabestatus je TV
- Getrennter Verlauf je TV
- Gleicher Titel auf unterschiedlichen TVs erlaubt
- Duplikat- und Wiederholungsschutz pro Ziel-TV
- Konfigurierbarer Standard-TV

## Playback und Fehlerbehandlung

SmartTube PartyQueue verarbeitet die von Home Assistant uebermittelten MediaSession-Daten und unterstuetzt:

- Normales Titelende
- Manuellen Skip in der Hostoberflaeche
- Externen Skip direkt in SmartTube
- Pause und Fortsetzen
- Idle-Fallback
- SponsorBlock-Spruenge am Videoende
- Wiedergabestart mit Bestaetigung
- Einmaligen automatischen Wiederholungsversuch
- Schutz vor Skip-Kaskaden

### Start-Guard

Nach jedem von PartyQueue ausgeloesten Titelstart werden verspaetete `idle`-Meldungen fuer einen kurzen Zeitraum ignoriert. Dadurch beendet eine SmartTube-Uebergangsmeldung nicht versehentlich den gerade gestarteten Titel.

### Playback-Watchdog

Nach einem Startbefehl wartet PartyQueue auf eine neue `playing`-Meldung. Wenn keine Bestaetigung eintrifft, wird der Startbefehl einmal wiederholt. Der bestehende Queue-Eintrag bleibt aktiv; es wird kein weiterer Titel ausgewaehlt. Ein haengender Home-Assistant-Webhook blockiert den Retry nicht.

## Architektur der V2.x-Versionen

```text
Gast- und Host-Browser
        |
        v
SmartTube PartyQueue
FastAPI + SQLite + WebSocket
        |
        v
Home-Assistant-Webhook
        |
        v
Android TV / ADB
        |
        v
SmartTube
```

### PartyQueue uebernimmt

- Weboberflaechen
- Partyverwaltung
- Queue und Playlists
- Upvotes und Hypes
- Wiedergabelogik
- Archiv und Exporte
- Diagnose und Recovery

### Home Assistant uebernimmt

- SmartTube-Startbefehl auf dem Ziel-TV
- MediaSession-Wiedergabestatus
- Uebermittlung von Status, Position und App-ID an PartyQueue

> In V2.x ist Home Assistant erforderlich. Fuer V3.0 ist eine direkte ADB-Anbindung geplant. Home Assistant soll danach als optionale Integration erhalten bleiben.

## Voraussetzungen

- Docker Engine oder kompatible Containerumgebung
- Docker Compose
- Home Assistant
- Android-TV-/ADB-Integration in Home Assistant
- SmartTube auf mindestens einem Zielgeraet
- YouTube Data API v3 Key
- Netzwerkverbindung zwischen PartyQueue, Home Assistant und Zielgeraeten

Optional:

- Portainer
- Reverse Proxy wie Caddy, Traefik oder Nginx Proxy Manager
- Eigene Domain fuer den Gastzugriff

## Schnellstart

### 1. Repository klonen

```bash
git clone <REPOSITORY-URL>
cd smarttube-partyqueue
```

### 2. Konfiguration anlegen

```bash
cp .env.example .env
```

Danach `.env` bearbeiten. Mindestens erforderlich sind:

- `YOUTUBE_API_KEY`
- `ADMIN_PASSWORD`
- `HA_URL`
- `DEFAULT_TV`
- `TV_DEVICES`

### 3. Container bauen und starten

```bash
docker compose up -d --build
```

### 4. Logs kontrollieren

```bash
docker compose logs --tail=100 -f
```

### 5. Health-Endpunkt pruefen

```bash
curl http://127.0.0.1:8787/api/health
```

Erwartete Antwort:

```json
{
  "ok": true,
  "version": "2.8.3"
}
```

## Konfiguration

Die vollstaendige Variablenreferenz befindet sich in [docs/configuration.md](docs/configuration.md).

Beispiel:

```env
TZ=Europe/Berlin
YOUTUBE_API_KEY=replace_me
HA_URL=http://homeassistant.local:8123
HA_WEBHOOK_ID=smarttube_partyqueue_play
ADMIN_PASSWORD=change-me
DEFAULT_TV=ke75
TV_DEVICES=xi4k|Xiaomi Gaestezimmer,ke75|KE75 Medienzimmer
```

## Home Assistant

Die vollstaendige Einrichtung ist in [docs/home-assistant.md](docs/home-assistant.md) beschrieben.

Mitgelieferte Vorlagen:

```text
home-assistant/
├── automation.yaml
├── playback-progress.yaml
├── rest-command.yaml
└── video-ended-example.yaml
```

Die TV-IDs in Home Assistant muessen exakt den Eintraegen in `TV_DEVICES` entsprechen.

## Verwendung

### Party vorbereiten

1. Hostoberflaeche aufrufen und anmelden.
2. Grundplaylist auswaehlen.
3. Zielgeraete freigeben und Standard-TV festlegen.
4. Wunschlimit und Wiederholungsschutz pruefen.
5. Neue Party starten oder bestehende Einstellungen klonen.

### Waehrend der Party

Gaeste geben ihren Namen ein, waehlen einen TV, suchen einen Titel oder verwenden eine YouTube-URL und fuegen den Wunsch hinzu. Offene Wuensche koennen per Upvote bewertet werden. Der laufende Titel kann einen Hype erhalten.

Der Host kontrolliert Queue und Wiedergabe. Das Debug-Panel wird nur bei Problemen benoetigt.

### Party abschliessen

1. `Party abschliessen` auswaehlen.
2. Offene Wuensche werden als `cancelled` gespeichert.
3. Die Party erscheint im Archiv.
4. HTML-, PDF-, CSV-, JSON- und M3U-Exporte stehen zur Verfuegung.

## Updates und Backups

### Update einer Quellcode-Installation

```bash
git pull
docker compose down
docker compose up -d --build
```

Die SQLite-Datenbank liegt im persistenten Datenverzeichnis und bleibt bei einem Container-Neubau erhalten.

Vor groesseren Updates wird ein Backup empfohlen:

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
```

## Diagnose

Siehe [docs/troubleshooting.md](docs/troubleshooting.md).

Containerlogs:

```bash
docker compose logs --tail=200 -f
```

Playback-Ereignisse filtern:

```bash
docker compose logs --since=10m \
  | grep PLAYBACK_DEBUG \
  > playback-debug.log
```

## Sicherheit

- `ADMIN_PASSWORD` vor dem ersten Start aendern.
- `.env` niemals in Git einchecken.
- YouTube-API-Key nicht oeffentlich teilen.
- Hostoberflaeche nicht ohne Zugriffsschutz oeffentlich bereitstellen.
- Bei oeffentlichem Zugriff HTTPS ueber einen Reverse Proxy verwenden.
- Regelmaessige Backups des Datenverzeichnisses erstellen.

Weitere Hinweise: [SECURITY.md](SECURITY.md)

## Versionshistorie

### V2.8.3 - Stabiler Home-Assistant-Release

- Playback-Watchdog unabhaengig vom Home-Assistant-Webhook
- Recovery nach SponsorBlock-Spruengen
- Pflichtname und Hype-System
- Archivsuche und Archivstatistiken
- HTML- und PDF-Recap
- Hostoberflaeche mit Tabs
- Auf echten Partys produktiv getestet

### V2.7

- Party-Lifecycle
- Partyarchiv und HTML-Recap
- Playback-Diagnose
- Start-Guard gegen Skip-Kaskaden

### V2.6

- Vollstaendige Playlist-Verwaltung
- Filter, Kopieren, Verschieben und Drag-and-drop

### V2.5

- Stabile Multi-TV-Playback-Basis
- Externe Skip-Erkennung
- YouTube-Kontingent
- Duplikat- und Wiederholungsschutz pro TV

Details: [CHANGELOG.md](CHANGELOG.md)

## Roadmap

### V3.0 - Standalone Core

- Home Assistant nicht mehr zwingend erforderlich
- Direkte ADB-Verbindung aus dem Container
- Wiedergabestatus direkt ueber ADB/MediaSession
- TV-Verwaltung in der WebUI
- Geraete in SQLite statt `TV_DEVICES`
- ADB-Kopplung und Verbindungstest
- Playback- und Geraeteoptionen in der WebUI
- Home Assistant als optionale Integration

### Distribution

- Automatischer Container-Build ueber GitHub Actions
- GitHub Container Registry
- Versionierte Images und `latest`
- Portainer-Stack ohne lokalen Build

### Spaeter moeglich

- Partyuebergreifende Analytics
- Gaeste- und Kuenstler-Rankings
- Hall of Fame
- Automatische Best-of-Playlist

## Entwicklung

- `main`: stabiler Release-Zweig
- `develop`: V3.0-Entwicklung

Weitere Informationen: [CONTRIBUTING.md](CONTRIBUTING.md)

## Lizenz

Dieses Projekt steht unter der [MIT License](LICENSE).
