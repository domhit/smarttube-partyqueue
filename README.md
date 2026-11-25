# SmartTube PartyQueue V4.5.0-rc1

Self-hosted Party-Musikqueue für SmartTube mit Gastoberfläche, Hostverwaltung, Playlists, Archiv/Recap und Multi-TV-Sync.

**V4.5.0-rc1** ist der Release Candidate des hardwaregetesteten REST-first-Playbackpfads. Getestet wurden natürliche Queue-Übergänge, SmartTube Events, SponsorBlock, Wunschpriorisierung, Multi-TV-Sync, Late Join, deaktivierte Geräte und REST-Recovery auf Android-TV-/Fire-TV-Geräten.

## Playback in V4.5

PartyQueue steuert SmartTube primär über die REST API des PartyQueue-SmartTube-Forks (Standardport `8090`). Der nächste Titel und eine Reserve werden direkt in SmartTube vorbereitet:

```text
current -> next -> reserve
```

SmartTube kann dadurch natürliche Titelübergänge selbst ausführen. PartyQueue überwacht Playback und Queue per REST, übernimmt geplante Übergänge und korrigiert Abweichungen. Die optionale SmartTube Event API liefert zusätzliche eindeutige Ereignisse wie `video_ended`, `user_skip` und `sponsorblock_skip`.

ADB bleibt als Bootstrap/Fallback erhalten, falls SmartTube oder seine REST API nicht erreichbar ist. Ein persistentes `./adb:/root/.android`-Volume ist deshalb weiterhin empfohlen.

## Empfohlene SmartTube-Einstellungen

Auf allen PartyQueue-Geräten möglichst identisch:
- Hintergrundwiedergabe/PiP passend zum Gerät aktivieren
- Videos fortlaufend abspielen
- Pause nach jedem Video: aus
- Stop nach jedem Video: aus
- REST API aktivieren und Zugangsdaten in PartyQueue unter **Host -> TVs** spiegeln

Decoder-, HDR-, Codec- und Audioeinstellungen dürfen gerätespezifisch bleiben.

## Entwicklung

- `main`: stabile Releases
- `develop` / `develop-v*`: laufende Entwicklung
- Tests: `pytest -q`, Python-/JavaScript-Syntax und Docker-Smoke-Build via GitHub Actions
