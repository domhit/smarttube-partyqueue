### Changelog

Alle wesentlichen Änderungen an SmartTube PartyQueue werden hier dokumentiert. Das Format orientiert sich an Keep a Changelog und Semantic Versioning.

#### [Unreleased]

#### [4.5.0-rc1] - 2026-11-25

##### Release Candidate
- Hardwaregetesteten V4.5 REST-first-Stand aus Alpha6 ohne neue Playback-Funktionen eingefroren.
- Dokumentation, Versionsangaben, GHCR-Hinweise und Troubleshooting auf den Release-Candidate-Stand vereinheitlicht.
- Veraltete V2.8.3-Screenshots und die versehentlich versionierte `source.zip` entfernt.
- `*.zip` in `.gitignore` aufgenommen, damit lokale Archive nicht erneut committed werden.

##### Validiert
- SmartTube REST Playback und Queue-Prefetch (`current -> next -> reserve`).
- SmartTube Events für Start, natürliches Ende, Skip und SponsorBlock.
- Wunschpriorisierung vor Grundplaylist-Fallbacks.
- Multi-TV-Sync, Late Join, Drift-Recovery und Follower-Recovery.
- Entfernen/deaktivieren von TVs ohne REST-Outage-Spam.
- 20-Sekunden Natural-End-Recovery als REST-Fallback.

#### [4.5.0-alpha6] - 2026-11-25

##### Fixed
- Deaktivierte oder aus der aktiven Party entfernte TVs werden nicht mehr als REST-Ausfall behandelt; Polling, Sync, Prefetch und Bootstrap werden für sie sauber gestoppt.
- Natural-End-Wartefenster auf 20 Sekunden erweitert; wenn SmartTube danach noch auf dem beendeten Titel steht, wird der bereits ausgewählte Folgetitel kontrolliert per REST gestartet.
- Natural-End-REST-Recovery wird mit `END_TRANSITION_REST_RECOVERY` eindeutig diagnostiziert.

##### Changed
- `QUEUE_PREFETCHED` wird nur noch bei tatsächlichem Add, Move oder geändertem Slot protokolliert.
- Wieder aufgenommenes TV-Monitoring wird explizit als `DEVICE_MONITORING_RESUMED` protokolliert.

#### [4.5.0-alpha5] - 2026-11-25

##### Fixed
- Prefetch und tatsächliche Next-Auswahl verwenden dieselbe zentrale Kandidatensortierung.
- Echte Wünsche werden vor Grundplaylist-Fallbacks abgespielt, auch wenn ein Fallback bereits eine niedrigere Queue-Position besitzt.
- Ein bereits in SmartTube vorbereiteter Wunsch wird beim Titelwechsel nicht mehr durch einen widersprüchlich ausgewählten Grundplaylist-Titel ersetzt.

##### Changed
- `NEXT_QUEUE_SELECTED` protokolliert zusätzlich die Quelle (`request` oder `base`).

#### [4.5.0-alpha4] - 2026-11-25

##### Fixed
- Queue-Prefetch pausiert während eines erkannten natürlichen SmartTube-Titelübergangs.
- Natural-End-Übergänge werden als `played` statt `skipped` abgeschlossen.

#### [4.5.0-alpha3] - 2026-11-25

##### Fixed
- Queue-Prefetch schließt das aktuell laufende Video zuverlässig aus.
- SmartTube-Queue-Matching verwendet die tatsächliche Reihenfolge von `items[]`.
- Nach Queue-Adds wird kurz auf die Sichtbarkeit des neuen Eintrags gewartet.

##### Changed
- Veraltete Home-Assistant- und Debug-Entwicklungsdateien entfernt.

