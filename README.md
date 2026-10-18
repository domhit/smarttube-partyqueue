# SmartTube PartyQueue V2.4.2

Hotfix für die Migration der Grundplaylist.

## Behoben

- Migration der alten Tabelle `base_play_history` von `base_item_id` auf `playlist_item_id`.
- Grundplaylist startet wieder, wenn die Wunschqueue leer ist.
- Der rote Fehler `no such column: playlist_item_id` tritt nicht mehr auf.
- Sichtbarer Schalter **Grundplaylist aktiv** in der aktiven Party.
- Leere Playlistnamen werden mit verständlicher Meldung abgelehnt.
- Bereits vorhandene Playlistnamen erzeugen einen verständlichen `409`-Hinweis statt eines SQLite-Tracebacks.

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

Keine manuelle Änderung an der Datenbank nötig. Die Migration läuft beim Containerstart.
