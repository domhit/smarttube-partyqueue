# SmartTube PartyQueue V2.3

## Neu in V2.3

- Vorstart des nächsten Titels standardmäßig 4 Sekunden vor Videoende
- SponsorBlock-kompatibel, weil die echte MediaSession-Position ausgewertet wird
- `idle` mit 2 Sekunden Wartezeit bleibt als Fallback erhalten
- Schutzfenster verhindert, dass das `idle` des alten Videos den bereits gestarteten Folgetitel überspringt
- Fortschrittsbalken und Zeitanzeige in Gast- und Hostansicht
- lokale Fortschrittsanimation zwischen den MediaSession-Updates
- grün/gelb/rote Suchkontingent-Ampel auf der Gästeseite

Alle Funktionen aus V2.2 bleiben erhalten: Multi-TV, gemeinsame zufällige Grundplaylist, YouTube-Playlist-Import, Verlauf, 50 Suchergebnisse und Quota-Zähler.

## Update

Die bestehende `.env` nicht überschreiben. Ergänzen:

```env
PRESTART_SECONDS=4
IDLE_FALLBACK_DELAY=2
PRESTART_IDLE_GUARD=10
```

Die bisherigen Gerätewerte bleiben unverändert.

Danach neu bauen:

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

## Home Assistant aktualisieren

1. Inhalt von `home-assistant/rest-command.yaml` in `configuration.yaml` übernehmen bzw. den vorhandenen `rest_command:`-Block erweitern.
2. `SYNOLOGY-IP` ersetzen.
3. Home Assistant neu starten.
4. Die bisherige Automation **SmartTube PartyQueue - Videoende erkennen** deaktivieren oder löschen.
5. Eine neue Automation aus `home-assistant/playback-progress.yaml` anlegen.
6. Die vorhandene Startautomation aus `home-assistant/automation.yaml` bleibt bestehen.

## Ablauf

Die MediaSession-Automation sendet Status und `media_position` an `/api/playback/progress`. Der Container vergleicht die Position mit der bereits in Queue und Grundplaylist gespeicherten `duration_seconds`.

- `playing` und Position >= Dauer minus 4 Sekunden: Folgetitel sofort starten
- `paused`: Position bleibt stehen, kein Vorstart
- `idle`: nach 2 Sekunden Folgetitel starten, falls der Vorstart nicht bereits erfolgt ist

## Suchampel für Gäste

- Grün: unter `YOUTUBE_SEARCH_WARNING_AT`
- Gelb: ab `YOUTUBE_SEARCH_WARNING_AT`
- Rot: ab `YOUTUBE_SEARCH_HARD_STOP_AT`; Linkeingabe bleibt möglich
