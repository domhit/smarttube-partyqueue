# SmartTube PartyQueue V2.7.0

V2.7.0 baut vollständig auf dem verifizierten V2.6.0-Stand auf. Die Playback-Funktionen `play()`, `nxt()`, `done()` und `progress()` sind byteidentisch zu V2.6.0.

## Party-Lifecycle

- **Party speichern** ändert nur die Einstellungen der laufenden Party.
- **Neue Party** beendet die laufende Party und startet eine frische Party mit Standardwerten.
- **Party klonen** beendet die laufende Party und startet eine neue Party mit denselben Einstellungen.
- **Party abschließen** setzt `active=0`, setzt `ended_at` und archiviert die Party endgültig.
- Der aktuell laufende Titel wird beim Abschluss als gespielt gespeichert.
- Offene Wünsche werden als `cancelled` gespeichert und nicht in die neue Party übernommen.
- Abgeschlossene Partys können nicht wieder geöffnet werden.
- Eine Datenbankmigration stellt sicher, dass höchstens eine Party aktiv ist.

## Partyarchiv

- Partyname, Startzeit, Endzeit und Dauer
- Anzahl gespielter Titel
- Anzahl erfüllter Wünsche
- Summe der Upvotes
- Exporte pro Party: Recap, CSV, JSON und M3U
- Archivdaten werden nur über den authentifizierten Admin-Endpunkt bereitgestellt.

## HTML Party Recap

- persönliche Einleitung mit Partyname, Datum, Startzeit und Dauer
- Statistik-Karten für Titel, Wünsche, Upvotes, Wunschgeber und Skips
- Meiste Wünsche
- Titel mit den meisten Upvotes
- Top-Künstler/Kanal
- Verhältnis Wünsche zu Grundplaylist
- Wunschgeber-Ranking
- chronologische Titelliste mit Startzeit, Wunschgeber, Votes, Quelle, Status und YouTube-Link
- responsives Layout und Druckansicht

## Erhalten aus V2.6.0

- funktionierende externe Skip-Erkennung
- Playlist-Verwaltung und Drag-and-drop
- Queue-Drag-and-drop
- Multi-TV-Duplikatschutz
- YouTube-API-Kontingent
- Trusted-Types-sicheres Userscript

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
docker compose logs --tail=100 -f
```

Die Datenbankmigration erfolgt automatisch. Keine Änderung an `.env`, Home Assistant oder Caddy erforderlich.
