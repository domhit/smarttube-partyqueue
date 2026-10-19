# SmartTube PartyQueue V2.5.2

V2.5.2 basiert vollständig auf dem verifizierten V2.5.1-Playback-Stand. Die Funktionen `play()`, `nxt()`, `done()` und `progress()` wurden nicht verändert.

## Neu

- Checkbox **Externe Skip-Erkennung aktiv** in der Hostansicht
- Einstellung wird aus der aktiven Party geladen und mit **Party speichern** gespeichert
- YouTube-API-Quota inklusive Cache-Treffern, Playlist-Aufrufen, Fehlern und Reset-Zeit
- Duplikat- und Wiederholungsschutz gelten pro Ziel-TV
- derselbe Titel kann gleichzeitig auf unterschiedlichen TVs eingeplant werden
- verbessertes Tampermonkey-Userscript mit TV-Auswahl, YouTube-Suchergebnisbuttons und Trusted-Types-sicherem Dialog

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
docker compose logs --tail=100 -f
```

Keine Änderung an `.env`, Datenbank oder Home Assistant erforderlich.
