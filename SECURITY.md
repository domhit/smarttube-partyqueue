# Sicherheit

## Unterstuetzte Version

Sicherheitskorrekturen werden derzeit fuer den aktuellen stabilen Release bereitgestellt.

| Version | Unterstuetzt |
|---|---|
| 2.8.x | Ja |
| < 2.8 | Nein |

## Sicherheitsproblem melden

Bitte Sicherheitsprobleme nicht als oeffentliches GitHub-Issue veroeffentlichen. Verwende stattdessen GitHub Private Vulnerability Reporting, sofern es fuer das Repository aktiviert ist, oder kontaktiere den Maintainer ueber einen privaten Kanal.

Bitte angeben:

- Betroffene Version
- Beschreibung der Schwachstelle
- Reproduktionsschritte
- Moegliche Auswirkungen
- Vorgeschlagene Korrektur, falls vorhanden

## Betriebshinweise

- `ADMIN_PASSWORD` aendern.
- `.env` nicht committen.
- YouTube-API-Key geheim halten.
- Hostoberflaeche nicht ungeschuetzt im Internet bereitstellen.
- HTTPS und Zugriffsbeschraenkungen am Reverse Proxy verwenden.
- Datenverzeichnis regelmaessig sichern.
- Gast- und Hostzugriff nach Moeglichkeit getrennt regeln.
