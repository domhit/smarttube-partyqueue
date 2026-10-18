# SmartTube PartyQueue V2.4.1

Hotfix für die V2.4-Weboberfläche.

## Behoben

- Hostformular wird nicht mehr bei jedem MediaSession-/WebSocket-Update zurückgesetzt.
- Eingaben für Partyname, Playlist, Standard-TV, Limit, Wiederholungsschutz, Upvotes und Skip-Erkennung bleiben bis zum Speichern erhalten.
- Nach einem Partywechsel wird das Formular weiterhin korrekt neu geladen.
- Gastseite funktioniert nun auch über unverschlüsseltes HTTP, wo `crypto.randomUUID()` nicht verfügbar ist.
- Gastseite behandelt fehlende Playback-Daten defensiv und zeigt Current/Queue trotzdem an.
- Userscript enthält `@description`, breitere YouTube-Matches und einen UUID-Fallback.

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

Keine Änderung an `.env`, Home-Assistant-Automationen oder Datenbank erforderlich.
