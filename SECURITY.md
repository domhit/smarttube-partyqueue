# Sicherheit

## Unterstützte Versionen

| Version | Sicherheitsupdates |
|---|---|
| 4.5.x | Ja, aktuelle stabile Version |
| 4.4.x | Nur kritische Korrekturen |
| < 4.4 | Nein |

## Sicherheitsproblem melden

Sicherheitsprobleme nicht als öffentliches Issue veröffentlichen. GitHub Private Vulnerability Reporting verwenden, sofern aktiviert, oder den Maintainer privat kontaktieren.

## Betriebshinweise

- `ADMIN_PASSWORD` vor dem ersten Start ändern.
- YouTube API Key, REST-Passwörter, SmartTube Event Token und ADB-Schlüssel geheim halten.
- Hostoberfläche nicht ungeschützt öffentlich bereitstellen.
- Bei externem Zugriff HTTPS und Zugriffsbeschränkungen am Reverse Proxy verwenden.
- `/app/data` und `/root/.android` sichern.
