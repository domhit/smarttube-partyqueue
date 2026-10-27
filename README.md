# SmartTube PartyQueue V4.4.3-alpha5

REST-only Alpha mit SmartTube-Queue-Prefetch. Der nächste PartyQueue-Titel wird über `/api/v1/queue/items` vorgeladen, direkt hinter den aktuellen Titel verschoben und beim automatischen Übergang ohne erneuten `/play`-Aufruf übernommen.

## Empfohlene SmartTube-Einstellungen

Für einen zuverlässigen Betrieb mit PartyQueue sollten auf allen verwendeten
SmartTube-Geräten folgende Einstellungen identisch gesetzt werden:

- **Allgemein → Hintergrundwiedergabe:** Bild-in-Bild bei Home/Back aktivieren
- **Player → Wiedergabemodus:** Videos fortlaufend abspielen
- **Player → Pause nach jedem Video:** deaktivieren
- **Player → Stop nach jedem Video:** deaktivieren
- **Player → Netzwerk-Engine:** Cronet

Video-, Audio- und Decoder-Voreinstellungen sollten dagegen nicht zwingend
zwischen verschiedenen Geräten synchronisiert werden. Fire TV, Xiaomi TV
Stick und unterschiedliche TV-Generationen können verschiedene Decoder-,
HDR-, Codec- und Audiofähigkeiten besitzen.

Für PartyQueue gilt grundsätzlich:

1. Wiedergabe soll nicht abbrechen.
2. SmartTube soll die vorbereitete Queue selbstständig abarbeiten.
3. PartyQueue überwacht und korrigiert die Wiedergabe.
4. MultiSync korrigiert Abweichungen zwischen den Geräten.

Dadurch kann die Wiedergabe auch bei einem vorübergehenden Netzwerk- oder
Sync-Problem möglichst selbstständig weiterlaufen.