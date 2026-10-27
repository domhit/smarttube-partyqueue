# Sicherheit

## Unterstützte Versionen

| Version | Sicherheitsupdates |
|---|---:|
| 3.0.x | Ja |
| 2.8.x | Nur kritische Korrekturen |
| < 2.8 | Nein |

## Sicherheitsproblem melden

Sicherheitsprobleme nicht als öffentliches Issue veröffentlichen. GitHub Private Vulnerability Reporting verwenden, sofern es für das Repository aktiviert ist, oder den Maintainer privat kontaktieren.

Bitte angeben:

- betroffene Version
- Beschreibung und Reproduktionsschritte
- mögliche Auswirkungen
- vorgeschlagene Korrektur, falls vorhanden

## Betriebshinweise

- `ADMIN_PASSWORD` vor dem ersten Start ändern.
- `.env`, YouTube API Key und ADB-Schlüssel geheim halten.
- Hostoberfläche nicht ungeschützt öffentlich bereitstellen.
- HTTPS und Zugriffsbeschränkungen am Reverse Proxy verwenden.
- Gast- und Hostzugriff nach Möglichkeit trennen.
- `/app/data` und `/root/.android` regelmäßig sichern.
- hochgeladene Banner als nicht vertrauenswürdige Eingaben behandeln; zugelassen sind JPG, PNG und WebP bis 5 MB.
