# Konfigurationsreferenz

SmartTube PartyQueue liest seine Einstellungen aus `.env`. Die Datei wird aus `.env.example` erstellt.

```bash
cp .env.example .env
```

## Grundkonfiguration

| Variable | Standard | Beschreibung |
|---|---:|---|
| `TZ` | `Europe/Berlin` | Zeitzone fuer Partyzeiten und Exporte |
| `YOUTUBE_API_KEY` | `replace_me` | YouTube Data API v3 Key |
| `HA_URL` | `http://homeassistant.local:8123` | Home-Assistant-Basis-URL |
| `HA_WEBHOOK_ID` | `smarttube_partyqueue_play` | Webhook-ID fuer den SmartTube-Start |
| `ADMIN_PASSWORD` | `change-me` | Passwort der Hostoberflaeche |
| `DATA_DIR` | `/app/data` | Pfad fuer SQLite und persistente Daten |

## Gaeste und Suche

| Variable | Standard | Beschreibung |
|---|---:|---|
| `MAX_VIDEO_MINUTES` | `12` | Maximale Laenge eines Wunschtitels |
| `MAX_REQUESTS_PER_GUEST` | `3` | Maximale offene Wuensche pro Gast |
| `SEARCH_CACHE_HOURS` | `168` | Cache-Dauer fuer Suchergebnisse |
| `SEARCH_MIN_LENGTH` | `3` | Mindestlaenge einer Suchanfrage |
| `SEARCH_RESULTS` | `50` | Maximale Zahl der Suchergebnisse |
| `YOUTUBE_SEARCH_DAILY_LIMIT` | `100` | Internes Tageslimit |
| `YOUTUBE_SEARCH_WARNING_AT` | `80` | Warnschwelle |
| `YOUTUBE_SEARCH_HARD_STOP_AT` | `98` | Harte Stoppschwelle |
| `BASE_PLAYLIST_RECENT_EXCLUDE` | `20` | Zahl zuletzt gespielter Basistitel, die vermieden werden |

## Playback

| Variable | Standard | Beschreibung |
|---|---:|---|
| `PRESTART_SECONDS` | `4` | Vorlauf vor der bekannten Videodauer |
| `IDLE_FALLBACK_DELAY` | `2` | Wartezeit vor der Verarbeitung eines dauerhaften `idle` |
| `PRESTART_IDLE_GUARD` | `10` | Schutz nach einem PartyQueue-Titelstart |
| `EXTERNAL_SKIP_MIN_PREVIOUS` | `30` | Mindestposition vor einem externen Skip |
| `EXTERNAL_SKIP_MAX_NEW` | `8` | Maximale neue Position nach einem externen Skip |
| `PLAY_CONFIRM_TIMEOUT` | `6` | Wartezeit bis zum automatischen Retry |
| `PLAY_RETRY_TIMEOUT` | `10` | Wartezeit nach dem Retry |
| `PLAY_WEBHOOK_TIMEOUT` | `5` | Timeout eines einzelnen Home-Assistant-Aufrufs |
| `PLAY_CONFIRM_MAX_POSITION` | `20` | Hoechste Position fuer eine neue Startbestaetigung |
| `SMARTTUBE_PACKAGE` | `org.smarttube.stable` | Android-Paketname von SmartTube |

## Geraete

| Variable | Beschreibung |
|---|---|
| `DEFAULT_TV` | ID des Standardgeraets |
| `TV_DEVICES` | Kommagetrennte Liste aus interner ID und Anzeigename |

Beispiel:

```env
DEFAULT_TV=ke75
TV_DEVICES=xi4k|Xiaomi Gaestezimmer,ke75|KE75 Medienzimmer,kd70|KD70 Schlafzimmer
```

Die internen IDs muessen mit den IDs in den Home-Assistant-Automationen uebereinstimmen.

## Persistenz

Das Compose-Setup bindet standardmaessig ein lokales Datenverzeichnis ein:

```yaml
volumes:
  - ./data:/app/data
```

In diesem Verzeichnis liegt die SQLite-Datenbank. Es sollte in die Backup-Strategie aufgenommen werden.
