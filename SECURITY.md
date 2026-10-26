# Security Policy

## Unterstützte Versionen

| Version | Support |
| --- | --- |
| 4.4.x | Ja |
| 4.3.x und älter | Nein, Upgrade auf V4.4.2 empfohlen |
| 3.x | Legacy, keine aktive Weiterentwicklung |

## Sicherheitsrelevante Hinweise

- Das Admin-Passwort nicht mit veröffentlichen.
- `data/` enthält die PartyQueue-Datenbank und sollte gesichert werden.
- `adb/` beziehungsweise `/root/.android` enthält private ADB-Schlüssel. Dieses Verzeichnis niemals veröffentlichen oder committen.
- Gastzugriff und Host-/Adminzugriff sollten im Reverse Proxy und in der Firewall getrennt werden.

Sicherheitsprobleme bitte nicht als öffentliches Issue mit Zugangsdaten, API-Keys oder privaten ADB-Schlüsseln melden.
