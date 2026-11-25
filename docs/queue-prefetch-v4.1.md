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
