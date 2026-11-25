# SmartTube PartyQueue V4.5.0

Self-hosted Party-Musikqueue fÃ¼r SmartTube mit GastoberflÃ¤che, Hostverwaltung, Playlists, Archiv/Recap und Multi-TV-Sync.

**V4.5.0** ist der Release Candidate des hardwaregetesteten REST-first-Playbackpfads. Getestet wurden natÃ¼rliche Queue-ÃœbergÃ¤nge, SmartTube Events, SponsorBlock, Wunschpriorisierung, Multi-TV-Sync, Late Join, deaktivierte GerÃ¤te und REST-Recovery auf Android-TV-/Fire-TV-GerÃ¤ten.

## Playback in V4.5

PartyQueue steuert SmartTube primÃ¤r Ã¼ber die REST API des PartyQueue-SmartTube-Forks (Standardport `8090`). Der nÃ¤chste Titel und eine Reserve werden direkt in SmartTube vorbereitet:

```text
current -> next -> reserve
```

SmartTube kann dadurch natÃ¼rliche TitelÃ¼bergÃ¤nge selbst ausfÃ¼hren. PartyQueue Ã¼berwacht Playback und Queue per REST, Ã¼bernimmt geplante ÃœbergÃ¤nge und korrigiert Abweichungen. Die optionale SmartTube Event API liefert zusÃ¤tzliche eindeutige Ereignisse wie `video_ended`, `user_skip` und `sponsorblock_skip`.

ADB bleibt als Bootstrap/Fallback erhalten, falls SmartTube oder seine REST API nicht erreichbar ist. Ein persistentes `./adb:/root/.android`-Volume ist deshalb weiterhin empfohlen.

## Empfohlene SmartTube-Einstellungen

Auf allen PartyQueue-GerÃ¤ten mÃ¶glichst identisch:
- Hintergrundwiedergabe/PiP passend zum GerÃ¤t aktivieren
- Videos fortlaufend abspielen
- Pause nach jedem Video: aus
- Stop nach jedem Video: aus
- REST API aktivieren und Zugangsdaten in PartyQueue unter **Host -> TVs** spiegeln

Decoder-, HDR-, Codec- und Audioeinstellungen dÃ¼rfen gerÃ¤tespezifisch bleiben.

## Entwicklung

- `main`: stabile Releases
- `develop` / `develop-v*`: laufende Entwicklung
- Tests: `pytest -q`, Python-/JavaScript-Syntax und Docker-Smoke-Build via GitHub Actions
