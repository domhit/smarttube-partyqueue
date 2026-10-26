# Migration von V3 auf V4.4.2

V4.4.2 ist der empfohlene Hauptstand von SmartTube PartyQueue. V3 bleibt als Legacy-Release erhalten, wird aber nicht mehr als aktuelle Architektur weiterentwickelt.

## Wesentliche Architekturänderung

V3 wurde stärker durch externe Steuerpfade geprägt. V4 steuert SmartTube direkt über die REST-API und verwendet die native SmartTube-Queue.

Der gewünschte Normalbetrieb ist:

```text
PartyQueue
→ aktueller Titel + zwei Folgetitel in SmartTube
→ SmartTube wechselt selbstständig zum nächsten Queue-Eintrag
→ PartyQueue übernimmt den neuen aktuellen Titel
→ Queue-Fenster wird wieder auf drei Titel ergänzt
```

ADB bleibt als Bootstrap- und Recovery-Pfad erhalten. Es wird insbesondere verwendet, wenn SmartTube beendet wurde oder zwar als Prozess/REST-Service erreichbar ist, der sichtbare Player aber nicht mehr aktiv ist.

## Vor der Migration

1. `data/` sichern.
2. `adb/` sichern.
3. Auf jedem TV denselben kompatiblen SmartTube-REST-Build installieren.
4. REST und ADB im Host-TV-Tab testen.
5. Die empfohlenen SmartTube-Wiedergabeeinstellungen aus der README übernehmen.

## Nach der Migration testen

- normalen Titelstart
- natürlichen Titelwechsel
- Skip direkt in SmartTube
- Skip über die Hostoberfläche
- `force-stop` von SmartTube
- zweimal Back beziehungsweise TV-Home-Menü
- Neustart des PartyQueue-Stacks während laufender Wiedergabe
- bei MultiSync zusätzlich Lead/Follower-Wechsel, parallelen Skip und Drift-Korrektur
