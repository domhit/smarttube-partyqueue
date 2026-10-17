# SmartTube PartyQueue V2.1

Selbst gehostete Party-Jukebox mit YouTube-Suche, getrennten Queues für mehrere Android-TVs und Wiedergabe in SmartTube über Home Assistant/ADB.

## Mehrere TVs konfigurieren

In `.env`:

```env
SMARTTUBE_PACKAGE=org.smarttube.stable
DEFAULT_TV=ke75
TV_DEVICES=ke75|KE75 Medienzimmer,kd70|KD70 Schlafzimmer
```

Format: `interne-id|Anzeigename`, mehrere Geräte mit Komma trennen. Die interne ID wird an Home Assistant als `target_tv` gesendet.

In `home-assistant/automation.yaml` die Zuordnung anpassen:

```yaml
target_entities:
  ke75: media_player.tv_game_adb
  kd70: media_player.schlafzimmer_tv_schlafzimmer
```

Die IDs links müssen exakt zu `TV_DEVICES` passen. Die Entity-IDs rechts sind deine Android-TV-ADB-Entitäten.

## Update einer vorhandenen Installation

```bash
cd /volume1/docker/smarttube-partyqueue
git pull
```

Danach `.env` um `DEFAULT_TV`, `TV_DEVICES` und den aktuellen Paketnamen ergänzen und den Portainer-Stack mit Build neu deployen. Die vorhandene SQLite-Datenbank wird beim Start automatisch um `target_tv` erweitert. Alte offene Einträge werden dem `DEFAULT_TV` zugeordnet.

## Verhalten

- Jedes TV-Gerät besitzt eine eigene Queue und einen eigenen aktuell laufenden Titel.
- Das gleiche Video darf gleichzeitig auf verschiedenen TVs eingeplant werden.
- Gastlimit und Duplikatschutz gelten pro TV.
- Gäste und Host wählen das Zielgerät in der Weboberfläche.
- Skip, Sortierung und Videoende wirken nur auf das ausgewählte Gerät.
- Die globale Queue-Sperre sperrt weiterhin alle Geräte gemeinsam.

## Start

```bash
cp .env.example .env
nano .env
docker compose up -d --build
```

Gastansicht: Port `8787`, Hostansicht: `/host`.
