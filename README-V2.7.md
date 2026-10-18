# SmartTube PartyQueue V2.7.0 Update

Diese Datei enthält ein Overlay für den bestehenden V2.6.0-Stand.

## Dateien ersetzen

- `app/main.py`
- `app/static/host.js`
- `app/static/host.html`

## Neue Partylogik

- **Party speichern** ändert nur die laufende Party.
- **Party abschließen** archiviert die Party endgültig. Der laufende Titel wird als gespielt abgeschlossen; offene Wünsche werden als `cancelled` verworfen.
- **Neue Party** schließt eine laufende Party nach Rückfrage ab und startet eine frische Party mit Standardwerten.
- **Party klonen** schließt die laufende Party ab und startet eine neue Party mit den gleichen Einstellungen, aber leerer Queue, History und Votes.
- Abgeschlossene Partys können nicht wieder aktiviert werden.
- Das Partyarchiv zeigt Start, Dauer, Titel, Wünsche und Votes sowie Exporte pro Party.

## HTML Party Recap

Enthält:

- Partyname, Datum, erste Titelzeit und Partydauer
- gespielte Titel, Wünsche, Upvotes, Wunschgeber und Skips
- Wunschgeber-Ranking
- Meiste Wünsche
- Titel mit den meisten Upvotes
- Top-Künstler/Kanal
- Verhältnis Wünsche zu Grundplaylist
- chronologische Titelliste mit Startzeit, Wunschgeber, Votes, Quelle, Status und YouTube-Link
- responsives Neon-Design und Druckansicht

CSV, JSON und M3U bleiben als technische Exporte erhalten.
