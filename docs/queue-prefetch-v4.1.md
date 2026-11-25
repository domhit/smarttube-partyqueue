# Queue Prefetch V4.5

PartyQueue hält je aktivem Gerät bis zu drei SmartTube-Einträge bereit:

```text
current -> next -> reserve
```

Regeln:
- `current` wird von SmartTube geliefert und nicht erneut per Queue-Add eingefügt.
- `next` und `reserve` stammen aus der PartyQueue-Datenbank.
- Das aktuell laufende Video wird bei der Kandidatenauswahl ausgeschlossen.
- Nach `queue add` wartet PartyQueue bis zu 1,5 Sekunden auf die eventual consistency der SmartTube-Queue.
- Für die Position innerhalb eines Queue-Snapshots gilt die Reihenfolge von `items[]`; `items[].index` kann unmittelbar nach Mutationen kurz veraltet sein.
- Gültige Future-Items werden nur entfernt, wenn sie außerhalb des aktuellen Sollfensters liegen.

Diagnoseereignisse: `QUEUE_PREFETCHED`, `QUEUE_ITEM_REMOVED`, `QUEUE_WINDOW_READY`, `QUEUE_PREFETCH_ERROR`.


### Einheitliche Auswahl ab V4.5.0-alpha6

Prefetch und tatsächlicher Titelstart verwenden dieselbe Sortierung:

1. explizite Admin-Priorität,
2. echte Wünsche vor Grundplaylist-Fallbacks,
3. Votes bei aktivierter Vote-Sortierung,
4. Queue-Position,
5. Datenbank-ID.

Dadurch kann ein bereits vorgeladener Grundplaylist-Titel einen später eingegangenen Wunsch nicht mehr beim tatsächlichen Titelwechsel überholen.


#### Natural-End-Recovery ab V4.5.0-alpha6

Nach `END_DETECTED` wartet PartyQueue bis zu 20 Sekunden darauf, dass SmartTube den vorbereiteten Folgetitel selbst aktiviert. Währenddessen bleiben Prefetch und Queue-Mutationen gesperrt. Bleibt SmartTube nach 20 Sekunden noch auf dem beendeten Titel, startet PartyQueue den bereits ausgewählten Folgetitel kontrolliert über REST und protokolliert `END_TRANSITION_REST_RECOVERY`.
