# Home-Assistant-Integration fuer V2.x

In den V2.x-Releases ist Home Assistant der Transportlayer zwischen PartyQueue und SmartTube.

## Datenfluss

```text
PartyQueue -> Home-Assistant-Webhook -> androidtv.adb_command -> SmartTube
SmartTube MediaSession -> Home-Assistant-Automation -> PartyQueue Progress API
```

## Mitgelieferte Dateien

```text
home-assistant/
├── automation.yaml
├── playback-progress.yaml
├── rest-command.yaml
└── video-ended-example.yaml
```

Die Dateien sind Vorlagen und muessen an die eigenen Entity-IDs, TV-IDs, Netzwerkadressen und SmartTube-Paketnamen angepasst werden.

## 1. Admin-Passwort in secrets.yaml

```yaml
partyqueue_admin_password: DEIN_SICHERES_PASSWORT
```

Der Wert muss mit `ADMIN_PASSWORD` in der PartyQueue `.env` uebereinstimmen.

## 2. REST-Command

Aus `home-assistant/rest-command.yaml` uebernehmen und anpassen:

```yaml
rest_command:
  partyqueue_playback_progress:
    url: "http://PARTYQUEUE-IP:8787/api/playback/progress"
    method: POST
    headers:
      X-Admin-Password: !secret partyqueue_admin_password
      Content-Type: application/json
    payload: >-
      {"target_tv":"{{ target_tv }}","state":"{{ playback_state }}",
      "media_position":{{ media_position|float(0) }},"app_id":"{{ app_id }}"}
```

## 3. Playback-Fortschritt

`home-assistant/playback-progress.yaml` sendet bei Aenderungen der Media-Player-Entitaeten:

- `playing`
- `paused`
- `idle`
- `media_position`
- `app_id`

Die Trigger-IDs müssen den in der PartyQueue-WebUI angelegten TV-IDs entsprechen.

Beispiel:

```yaml
triggers:
  - trigger: state
    entity_id: media_player.mein_android_tv
    id: wohnzimmer
```

Dazu passend wird in der PartyQueue-WebUI ein TV mit der internen ID `wohnzimmer` und dem Modus `Home Assistant` angelegt.

## 4. SmartTube-Startautomation

`home-assistant/automation.yaml` stellt den Webhook `smarttube_partyqueue_play` bereit und fuehrt je Ziel-TV einen ADB-Befehl aus:

```text
am start -a android.intent.action.VIEW \
  -d "https://www.youtube.com/watch?v=VIDEO_ID" \
  org.smarttube.stable
```

Die Webhook-ID muss mit `HA_WEBHOOK_ID` uebereinstimmen.

## 5. Home Assistant neu laden

Nach dem Einbau:

1. YAML-Konfiguration pruefen.
2. Automationen neu laden oder Home Assistant neu starten.
3. PartyQueue-Container neu starten.
4. Host- und Gastseite per Hard-Reload aktualisieren.

## 6. Funktionstest

1. Im PartyQueue-Host einen TV auswaehlen.
2. `Start` auswaehlen.
3. Pruefen, ob SmartTube den Titel oeffnet.
4. Debug-Tab beobachten.
5. Erwartete Ereignisse:

```text
PLAY_DISPATCHED
PLAY_REQUEST
PLAY_WEBHOOK_OK
PLAY_CONFIRM_WAIT
PLAY_CONFIRMED
```

Wenn keine Bestaetigung kommt, wird einmal `PLAY_RETRY` ausgeloest.

## Sicherheit

Der mitgelieferte Webhook verwendet `local_only: true`. Die Hostoberflaeche sollte trotzdem nicht ungeschuetzt oeffentlich bereitgestellt werden.
