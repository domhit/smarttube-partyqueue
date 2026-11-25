## Changelog

Alle wesentlichen Änderungen an SmartTube PartyQueue werden hier dokumentiert. Das Format orientiert sich an Keep a Changelog und Semantic Versioning.

### [Unreleased]

### [4.5.0-alpha3] - 2026-11-25

#### Fixed
- Queue-Prefetch schließt das aktuell laufende Video zuverlässig aus.
- SmartTube-Queue-Matching verwendet die tatsächliche Reihenfolge von `items[]` statt eines möglicherweise verzögerten `index`-Felds.
- Nach Queue-Adds wird bis zu 1,5 Sekunden auf Sichtbarkeit des neuen Eintrags gewartet.
- Gültige Future-Queue-Einträge werden nicht mehr unnötig entfernt und erneut hinzugefügt.

#### Changed
- Veraltete Home-Assistant- und Debug-Entwicklungsdateien entfernt.
- Architektur-, Migrations- und Queue-Prefetch-Dokumentation auf den REST-first-Stand von V4.5 aktualisiert.

### [4.5.0-alpha2] - 2026-10-28

#### Added
- SmartTube Event API v1 mit `session_id` und Event-Token.
- REST-basierter SmartTube-Queue-Prefetch für `current + next + reserve`.
- ADB-Bootstrap/Fallback bei nicht erreichbarer SmartTube REST API.

#### Changed
- Pause/Resume-Events dienen nur als Telemetrie; Queue-/Historienentscheidungen kommen vom Lead.
- REST ist der primäre Playback-Transport.

