# V2.7.2 Skip Hotfix

## Behoben

- Auswahl `Externe Skip-Erkennung aktiv` in der Party-Konfiguration wiederhergestellt.
- Einstellung wird wieder geladen und mit `Party speichern` gespeichert.
- Nach einem manuellen, natürlichen oder extern erkannten Skip wird der alte MediaSession-Fortschritt verworfen.
- Für die Startphase des nächsten SmartTube-Titels gilt der vorhandene Guard-Zeitraum.
- Ein alter hoher Positionswert des vorherigen Titels kann den nächsten Titel daher nicht erneut als Skip interpretieren.

## Erwartetes Verhalten

- PartyQueue-Skip überspringt exakt einen Titel.
- Ein externer SmartTube-/Fernbedienungs-Skip wird nur erkannt, wenn die Option aktiviert ist.
- Pause, SponsorBlock und normale Titelwechsel lösen keine Skip-Kaskade aus.
