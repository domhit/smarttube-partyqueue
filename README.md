# SmartTube PartyQueue V2.6.0

V2.6.0 baut vollständig auf dem verifizierten V2.5.2-Stand auf. Die Playback-Funktionen `play()`, `nxt()`, `done()` und `progress()` sind byteidentisch zu V2.5.2 und damit zur funktionierenden V2.5.1-Engine.

## Playlist-Verwaltung

- Titel und Kanal filtern
- Titelanzahl, aktive Titel und Gesamtlaufzeit anzeigen
- sichtbare Titel gemeinsam auswählen
- ausgewählte Titel in eine andere Playlist kopieren oder verschieben
- vorhandene Duplikate im Ziel überspringen
- Titel aktivieren oder deaktivieren
- Titel per Drag-and-drop sortieren
- Erstellen, Duplizieren, Umbenennen, Löschen, Einzelimport und YouTube-Playlist-Import bleiben erhalten

## Wunschqueue

- Drag-and-drop im Host
- Pfeiltasten bleiben als Touch-Fallback erhalten
- `Als Nächstes` und Entfernen bleiben erhalten
- Queue und Sortierung bleiben pro Ziel-TV getrennt

## Aus V2.5.2 erhalten

- funktionierende externe Skip-Erkennung und Checkbox
- YouTube-API-Kontingent
- Duplikat- und Wiederholungsschutz pro TV
- Trusted-Types-sicheres Tampermonkey-Userscript

## Update

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
docker compose down
docker compose up -d --build
docker compose logs --tail=100 -f
```

Keine Änderung an `.env`, Datenbank oder Home Assistant erforderlich.
