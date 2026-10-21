# SmartTube PartyQueue

SmartTube PartyQueue ist eine eigenständige Musik-Wunschplattform für Partys mit SmartTube auf Android TV und Fire TV. Gäste suchen Titel über eine mobile Weboberfläche, senden Wünsche an einen freigegebenen TV, stimmen über offene Wünsche ab und vergeben Hypes für den laufenden Titel. Der Host verwaltet Partys, Playlists, Geräte, Warteschlangen, Archive, Exporte und die Playback-Diagnose.

**Aktueller Release:** V3.1.0  
**Status:** Stable  
**Architektur:** Docker + FastAPI + SQLite + direktes ADB; Home Assistant optional  
**Container:** `ghcr.io/domhit/smarttube-partyqueue:3.1.0` oder `:latest`

[Changelog](CHANGELOG.md) · [Konfiguration](docs/configuration.md) · [Architektur](docs/architecture.md) · [Home Assistant](docs/home-assistant.md) · [Fehlerbehebung](docs/troubleshooting.md) · [Sicherheit](SECURITY.md)

## Highlights von V3.1.0

- Standalone-Betrieb ohne Home Assistant
- direkte SmartTube-Steuerung über ADB
- direkte MediaSession-Auswertung über `dumpsys media_session`
- TV-Verwaltung, ADB-Pairing und Verbindungstest in der WebUI
- persistente ADB-Schlüssel über `/root/.android`
- mobile Gastoberfläche mit Enter-Unterstützung und Ergebnis-Karten
- optionales Partybanner auf der Gastseite
- Multi-TV-Queues, Upvotes, Hypes und Grundplaylists
- Partyarchiv mit HTML-, PDF-, CSV-, JSON- und M3U-Export
- Playback-Watchdog, Start-Guard, Idle-Fallback und Skip-Erkennung
- Multi-Arch-Images für `linux/amd64` und `linux/arm64` über GHCR
- Betrieb mit Docker Compose oder Portainer ohne lokalen Image-Build

## Voraussetzungen

- Docker Engine, Docker Compose oder Portainer
- SmartTube auf mindestens einem Android-TV- oder Fire-TV-Gerät
- ADB-Zugriff auf die Zielgeräte
- YouTube Data API v3 Key für Suche und Playlist-Import
- Netzwerkverbindung vom Container zu den Zielgeräten

Optional:

- Home Assistant als alternativer Transport für einzelne Geräte
- Reverse Proxy wie Caddy, Traefik oder Nginx Proxy Manager
- HTTPS und getrennte Zugriffsregeln für Gast- und Hostoberfläche

## Schnellstart mit GHCR

### 1. Arbeitsverzeichnis anlegen

```bash
mkdir -p smarttube-partyqueue/data smarttube-partyqueue/adb
cd smarttube-partyqueue
```

### 2. `.env` anlegen

```env
ADMIN_PASSWORD=change-me
DATA_DIR=/app/data
```

`ADMIN_PASSWORD` vor dem ersten Start ändern.

### 3. Compose-Datei anlegen

```yaml
services:
  smarttube-partyqueue:
    image: ghcr.io/domhit/smarttube-partyqueue:3.1.0
    container_name: smarttube-partyqueue
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8787:8000"
    volumes:
      - ./data:/app/data
      - ./adb:/root/.android
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### 4. Starten

```bash
docker compose pull
docker compose up -d
```

### 5. Einrichten

1. Hostoberfläche öffnen: `http://SERVER-IP:8787/host`
2. Mit `ADMIN_PASSWORD` anmelden.
3. Unter **Einstellungen** den YouTube API Key speichern.
4. Unter **TVs** ein Gerät anlegen.
5. Für direktes ADB das Gerät koppeln und die Verbindung testen.
6. Eine Party starten und die Gastseite unter `http://SERVER-IP:8787/` öffnen.

Healthcheck:

```bash
curl http://127.0.0.1:8787/api/health
```

Erwartet:

```json
{"ok":true,"version":"3.1.0"}
```

## Portainer

In Portainer unter **Stacks → Add stack → Web editor** den Inhalt aus `docker-compose.ghcr.yml` einfügen. Für reproduzierbare Installationen `3.1.0` verwenden. `latest` folgt dem aktuellen stabilen Release.

Persistente Volumes:

- `./data:/app/data`: SQLite-Datenbank und Partybanner
- `./adb:/root/.android`: private ADB-Schlüssel

Bei einem Update **Pull latest image** aktivieren und den Stack neu deployen. Die beiden Verzeichnisse dürfen dabei nicht gelöscht werden.

## Bedienung

### Gastoberfläche

- Name und Ziel-TV auswählen
- per Suchbegriff oder YouTube-Link wünschen
- Suche und URL-Eingabe mit Enter absenden
- offene Wünsche upvoten
- laufenden Titel hypen
- aktuellen Titel und Fortschritt verfolgen

### Hostoberfläche

Die Hostoberfläche umfasst sechs Bereiche:

- **Party:** aktive Party, Grundplaylist, freigegebene TVs, Banner und Queue
- **Playlist:** Playlists, YouTube-Import, Aktivstatus und Drag-and-drop
- **Archiv:** abgeschlossene Partys, Rankings und Exporte
- **TVs:** Geräte, Transportmodus, ADB-Pairing und Verbindungstest
- **Einstellungen:** YouTube-, Playback-, ADB- und optionale HA-Parameter
- **Debug:** Playback-Zustände und strukturierte Diagnoseereignisse

## Multi-TV-Sync

In den Party-Einstellungen kann **Multi-TV-Sync** aktiviert werden. Der Standard-TV ist der Lead. Wünsche werden einer gemeinsamen Queue zugeordnet und gleichzeitig auf allen für die Party freigegebenen Geräten gestartet.

Der Lead bestimmt Wiedergabestatus, Pause, Fortsetzen, Skip und Titelende. ADB-Follower übernehmen Pause und Fortsetzen. Vorauslaufende Follower werden bei Überschreitung der konfigurierten Drift-Toleranz kurz pausiert und anschließend fortgesetzt. Zurückliegende Follower werden diagnostiziert, aber nicht automatisch vorgespult, da Android über die verwendete ADB-Schnittstelle keinen zuverlässigen app-unabhängigen Seek-Befehl bereitstellt.

Bei aktivem Sync oder nur einem freigegebenen TV wird die TV-Auswahl auf der Gastseite ausgeblendet. Ist das YouTube-Suchkontingent aufgebraucht, wird die Suche deaktiviert und der Gast auf den weiterhin möglichen URL-Import hingewiesen.

## Playback und Fehlerbehandlung

PartyQueue startet SmartTube direkt über ADB oder optional über einen Home-Assistant-Webhook. Bei ADB-Geräten liest PartyQueue Status und Position direkt aus Android MediaSession.

Sicherheitsmechanismen der Playback-Engine:

- Start-Guard gegen verspätete Idle-Meldungen
- Startbestätigung mit einmaligem Retry
- Ende-Erkennung über Position und Videodauer
- Idle-Fallback
- Erkennung externer SmartTube-Skips
- SponsorBlock-tolerante Übergänge
- getrennte Zustände und Queues je TV

## Konfiguration

Die `.env` enthält nur Bootstrap-Werte. TVs und Laufzeiteinstellungen werden in der WebUI gepflegt und in SQLite gespeichert. Details stehen in [docs/configuration.md](docs/configuration.md).

Die früheren Variablen `DEFAULT_TV` und `TV_DEVICES` werden nicht mehr verwendet.

## Updates und Backups

Vor einem Update:

```bash
cp data/partyqueue.db data/partyqueue-backup-$(date +%Y%m%d-%H%M).db
cp -a adb adb-backup-$(date +%Y%m%d-%H%M)
```

Update mit GHCR:

```bash
docker compose pull
docker compose up -d
```

Die ADB-Schlüssel sind vertraulich. Das Verzeichnis `adb/` niemals veröffentlichen oder committen.

## Entwicklung

Lokaler Build:

```bash
cp .env.example .env
docker compose up -d --build
```

Syntaxprüfungen:

```bash
python -m py_compile app/*.py
node --check app/static/host.js
node --check app/static/guest.js
node --check userscript/partyqueue.user.js
```

Branchmodell:

- `main`: aktueller stabiler Release
- `develop`: Entwicklung des nächsten Releases
- `feature/*`: neue Funktionen
- `fix/*`: Fehlerkorrekturen

## Roadmap

Mögliche nächste Schritte für V3.1:

- weitere mobile UX-Verbesserungen
- Banner in HTML- und PDF-Recaps
- zusätzliche Tests und automatisierte Release-Prüfungen
- partyübergreifende Analytics und Best-of-Playlists

## Lizenz

Dieses Projekt steht unter der [MIT License](LICENSE).
