# SmartTube PartyQueue V2.5.2

## Neu

- YouTube-API-Verbrauch im Host-Dashboard wieder sichtbar
- Suchaufrufe, geschätzte Rest-Suchen, Cache-Treffer, Playlist-Aufrufe, Fehler und Reset-Zeit
- grün/gelb/rote Quota-Anzeige
- Duplikat- und Wiederholungsschutz jetzt pro Party **und Ziel-TV**
- derselbe Titel darf gleichzeitig auf unterschiedlichen TVs eingeplant werden
- derselbe Titel bleibt auf demselben TV eindeutig

## Tampermonkey

- PartyQueue-Button weiterhin auf Watch-Seiten
- PartyQueue-Button direkt an YouTube-Suchergebnissen
- optionaler Rechtsklick auf einen YouTube-Videolink öffnet die Zielauswahl
- `Shift + Rechtsklick` öffnet weiterhin das normale Browser-Kontextmenü
- freigegebene Zielgeräte erscheinen als echte Buttons
- bei nur einem freigegebenen TV wird ohne Dialog direkt hinzugefügt
- zuletzt gewähltes Gerät wird grün hervorgehoben
- Toasts statt blockierender Erfolgs-Alerts
- kompatibel mit YouTubes SPA-Navigation

Vor Verwendung im Userscript weiterhin die Adresse anpassen:

```javascript
const PARTYQUEUE = 'http://partyqueue.local:8787';
```

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

Keine Änderung an `.env`, Home Assistant oder SQLite nötig.
