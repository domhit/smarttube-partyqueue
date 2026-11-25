# Sicherheit

## UnterstÃ¼tzte Versionen

| Version | Sicherheitsupdates |
|---|---|
| 4.5.x | Ja, aktueller Release Candidate |
| 4.4.x | Nur kritische Korrekturen |
| < 4.4 | Nein |

## Sicherheitsproblem melden

Sicherheitsprobleme nicht als Ã¶ffentliches Issue verÃ¶ffentlichen. GitHub Private Vulnerability Reporting verwenden, sofern aktiviert, oder den Maintainer privat kontaktieren.

## Betriebshinweise

- `ADMIN_PASSWORD` vor dem ersten Start Ã¤ndern.
- YouTube API Key, REST-PasswÃ¶rter, SmartTube Event Token und ADB-SchlÃ¼ssel geheim halten.
- HostoberflÃ¤che nicht ungeschÃ¼tzt Ã¶ffentlich bereitstellen.
- Bei externem Zugriff HTTPS und ZugriffsbeschrÃ¤nkungen am Reverse Proxy verwenden.
- `/app/data` und `/root/.android` sichern.
