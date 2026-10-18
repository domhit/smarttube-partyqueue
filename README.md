# SmartTube PartyQueue V2.4

## Neu

- Party-Sitzungen mit Name, eigener History und aktivem Grundplaylist-Profil
- Admin-Freigabe der Abspieler; Gäste sehen nur freigegebene Geräte
- sichtbarer Queue-Sperrstatus in Host- und Gastansicht
- Wiederholungsschutz für die letzten N Titel einer Party
- benannte Grundplaylists
- Wunschlimit pro Party, `0` bedeutet unbegrenzt
- Upvotes; optional nach Votes sortierte Wunschqueue
- Toast-Overlays zusätzlich zu persistenten Meldungen
- HTML-, CSV-, JSON- und M3U-Export der Party-History
- Statistik: gesamt, gewünscht, übersprungen und Votes
- Host-Skip
- optionale Erkennung eines externen SmartTube-Skips über starken Positionsrücksprung
- dynamisches Tampermonkey-Script mit aktueller Party, Sperrstatus und freigegebenen TVs

## Update

Bestehende `.env` nicht überschreiben. Optional ergänzen:

```env
EXTERNAL_SKIP_MIN_PREVIOUS=30
EXTERNAL_SKIP_MAX_NEW=8
```

Dann neu bauen:

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

SQLite wird automatisch migriert. Die bisherige Grundplaylist wird nach `Party allgemein` übernommen.

## Bedienung

1. In `/host` anmelden.
2. Aktive Party konfigurieren oder **Neue Party** wählen.
3. Grundplaylist, erlaubte Abspieler, Standard-TV, Wunschlimit und Wiederholungsschutz einstellen.
4. `Wunschlimit = 0` schaltet das Limit aus.
5. `Wiederholungsschutz = 0` deaktiviert die Prüfung.
6. Die externe SmartTube-Skip-Erkennung zunächst nur testweise aktivieren. Rückspulen von über 30 Sekunden auf unter 8 Sekunden kann ebenfalls als Skip erkannt werden.

## Tampermonkey

In `userscript/partyqueue.user.js` die Konstante `PARTYQUEUE` auf die echte interne Adresse setzen. Das Script lädt die aktive Party dynamisch und zeigt nur freigegebene Abspieler.

## Export

Die Hostseite bietet HTML, CSV, JSON und M3U. Der HTML-Export enthält anklickbare YouTube-Titel. Exporte sind admin-geschützt.
