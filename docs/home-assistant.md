# Optionale Home-Assistant-Integration

SmartTube PartyQueue V3 benötigt Home Assistant nicht. Direkte ADB-Geräte werden vollständig durch PartyQueue gesteuert und überwacht.

Home Assistant kann weiterhin als alternativer Transport für einzelne TVs verwendet werden.

## Datenfluss im HA-Modus

```text
PartyQueue -> Home-Assistant-Webhook -> androidtv.adb_command -> SmartTube
SmartTube MediaSession -> Home-Assistant-Automation -> PartyQueue Progress API
```

## Einrichtung

1. In PartyQueue unter **TVs** ein Gerät mit Modus **Home Assistant** anlegen.
2. Die interne TV-ID muss der Trigger-ID der Automation entsprechen.
3. `ha_url` und `ha_webhook_id` unter **Host → Einstellungen** konfigurieren.
4. Das Admin-Passwort in Home Assistant als Secret hinterlegen.

```yaml
partyqueue_admin_password: DEIN_SICHERES_PASSWORT
```

## Progress-REST-Command

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

Vorlagen liegen unter `home-assistant/` und müssen an die eigenen Entity-IDs und Netzwerkadressen angepasst werden.

## Funktionstest

Im Debug-Tab werden bei erfolgreichem Start typischerweise folgende Ereignisse sichtbar:

```text
PLAY_DISPATCHED
PLAY_REQUEST
PLAY_WEBHOOK_OK
PLAY_CONFIRM_WAIT
PLAY_CONFIRMED
```

Bei einem ADB-Gerät werden Fortschrittsmeldungen aus Home Assistant bewusst ignoriert, damit nicht zwei Statusquellen gegeneinander arbeiten.
