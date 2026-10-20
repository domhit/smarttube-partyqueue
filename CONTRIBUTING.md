# Mitwirken an SmartTube PartyQueue

Vielen Dank fuer das Interesse an SmartTube PartyQueue.

## Branchmodell

- `main`: stabiler, produktiv getesteter Stand
- `develop`: Entwicklung der naechsten Hauptversion
- Feature-Branches: `feature/<kurze-beschreibung>`
- Bugfix-Branches: `fix/<kurze-beschreibung>`

## Entwicklungsumgebung

```bash
git clone https://github.com/domhit/smarttube-partyqueue
cd smarttube-partyqueue
cp .env.example .env
docker compose up -d --build
```

## Aenderungen testen

Vor einem Pull Request mindestens pruefen:

```bash
python -m py_compile app/*.py
node --check app/static/host.js
node --check app/static/guest.js
node --check userscript/partyqueue.user.js
```

Ausserdem:

- Health-Endpunkt antwortet mit der erwarteten Version.
- Container startet ohne Fehler.
- Host- und Gastoberflaeche laden nach einem Hard-Reload.
- Bestehende Datenbank wird nicht unbeabsichtigt geloescht.
- Aenderungen an der Playback-Engine werden mit dem Debug-Panel verifiziert.

## Pull Requests

Ein Pull Request sollte enthalten:

- Problem oder Ziel
- Technische Loesung
- Betroffene Dateien
- Durchgefuehrte Tests
- Screenshots bei UI-Aenderungen
- Relevante Diagnoseereignisse bei Playback-Aenderungen

## Commit-Nachrichten

Beispiele:

```text
feat: add direct adb device management
fix: prevent duplicate playback retry
refactor: isolate playback transport layer
docs: document home assistant setup
chore: publish container image
```

## Fehlerberichte

Bitte angeben:

- PartyQueue-Version
- Geraetetyp und Betriebssystem
- SmartTube-Version
- Betroffener TV
- Schritte zur Reproduktion
- Erwartetes und tatsaechliches Verhalten
- Relevanter Debug-JSON-Ausschnitt
- Dockerlogs mit `PLAYBACK_DEBUG`

Keine Passwoerter, API-Schluessel, privaten Domains oder oeffentlichen IP-Adressen posten.
