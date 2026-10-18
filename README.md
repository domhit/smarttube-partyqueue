# SmartTube PartyQueue V2.5

## Playlist-Verwaltung neu strukturiert

Die einer Party zugeordnete Grundplaylist und die im Adminbereich bearbeitete Playlist sind vollständig getrennt.

- **Aktive Party → Verwendete Grundplaylist** ändert sich erst mit **Party speichern**.
- **Playlist-Verwaltung → Bearbeitete Playlist** kann unabhängig gewechselt werden.
- Eine neue Playlist ist leer.
- **Duplizieren** kopiert alle Titel in eine neue Playlist.
- Playlists können umbenannt und gelöscht werden.
- Einer Party zugeordnete Playlists können nicht gelöscht werden.
- Titel können per einzelner YouTube-URL, YouTube-Playlist-Import oder aus dem Verlauf hinzugefügt werden.
- Dropdowns zeigen die Titelanzahl an.

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

Keine `.env`- oder Home-Assistant-Änderung nötig. Bestehende Daten werden weiterverwendet.
