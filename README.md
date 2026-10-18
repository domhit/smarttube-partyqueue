# SmartTube PartyQueue V2.6.0

## Playlist-Verwaltung fertiggestellt

- Titel und Kanal filtern
- Titelanzahl, aktive Titel und Gesamtlaufzeit anzeigen
- sichtbare Titel gemeinsam auswählen
- ausgewählte Titel in eine andere Playlist kopieren
- ausgewählte Titel in eine andere Playlist verschieben
- vorhandene Duplikate im Ziel werden übersprungen
- Titel einzeln aktivieren oder deaktivieren
- Playlist-Reihenfolge per Drag-and-drop ändern
- bestehendes Erstellen, Duplizieren, Umbenennen, Löschen, Einzelimport und YouTube-Playlist-Import bleiben erhalten

## Wunschqueue

- Drag-and-drop für die Host-Queue
- Pfeiltasten bleiben als Touch-Fallback erhalten
- `Als Nächstes` und `Entfernen` bleiben erhalten
- Sortierung bleibt pro Ziel-TV getrennt

## Userscript

- Version 2.6.0
- Trusted-Types-sicher, ohne `innerHTML`
- YouTube-Suchergebnisbuttons, Rechtsklick und TV-Auswahldialog bleiben erhalten

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
```

Keine Änderung an `.env`, Home Assistant oder der bestehenden Datenbank erforderlich.
