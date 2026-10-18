# SmartTube PartyQueue V2.5.1

## Behoben

- Fortschrittsbalken und Zeitanzeige in Gast- und Hostansicht wiederhergestellt.
- Fortschritt läuft zwischen den MediaSession-Updates flüssig weiter.

## Queue-Management für den Host

- Titel nach oben verschieben
- Titel nach unten verschieben
- Titel als Nächstes markieren
- Titel aus der Queue entfernen

Eine manuell sortierte Queue erhält Vorrang vor der Upvote-Sortierung. Neue, noch nicht manuell sortierte Wünsche bleiben dahinter weiterhin nach Upvotes und Eingangszeit sortiert.

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

Die Datenbank wird automatisch um `admin_priority` erweitert. Keine Änderung an `.env` oder Home Assistant nötig.
